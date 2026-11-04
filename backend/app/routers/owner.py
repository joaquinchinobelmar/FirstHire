import hashlib
import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .. import companies_house, geo, services, wages
from ..ai import owner_agent
from ..ai.schemas import PlanStep
from ..db import dumps, get_db, loads, log_access
from ..security import require_role

router = APIRouter(prefix="/api/owner", tags=["owner"])
owner = require_role("owner")


def _firm(conn: sqlite3.Connection, user: dict) -> sqlite3.Row:
    firm = services.firm_for_owner(conn, user["id"])
    if not firm:
        raise HTTPException(404, "No firm linked to this account")
    return firm


def _shift(month: str, delta: int) -> str:
    y, m = map(int, month.split("-"))
    idx = y * 12 + (m - 1) + delta
    return f"{idx // 12:04d}-{idx % 12 + 1:02d}"


def _impact(metrics: list[dict], insights: list[dict]) -> list[dict]:
    """Code-calculated before/after comparison for every implemented AI suggestion."""
    by_month = {m["month"]: m for m in metrics}
    out = []
    for i in insights:
        start = i.get("implemented_at")
        if i["status"] != "implemented" or not start:
            continue
        before = [by_month[_shift(start, -k)] for k in (1, 2, 3) if _shift(start, -k) in by_month]
        after = [by_month[_shift(start, k)] for k in (0, 1, 2) if _shift(start, k) in by_month]
        if not before or not after:
            continue
        avg = lambda rows, key: sum(r[key] for r in rows) / len(rows)  # noqa: E731
        rb, ra = avg(before, "revenue"), avg(after, "revenue")
        cb, ca = avg(before, "customers"), avg(after, "customers")
        out.append({
            "insight_id": i["id"], "title": i["title"], "month": start,
            "revenue_before": round(rb), "revenue_after": round(ra), "revenue_change_pct": round((ra - rb) / rb * 100, 1),
            "customers_before": round(cb), "customers_after": round(ca), "customers_change_pct": round((ca - cb) / cb * 100, 1),
        })
    return out


def _insight_dict(r: sqlite3.Row) -> dict:
    return dict(r)


@router.get("/dashboard")
def dashboard(user: dict = Depends(owner), conn: sqlite3.Connection = Depends(get_db)):
    firm = _firm(conn, user)
    metrics = [dict(m) for m in conn.execute(
        "SELECT month, revenue, customers FROM firm_metrics WHERE firm_id = ? ORDER BY month", (firm["id"],)).fetchall()]
    insights = [_insight_dict(r) for r in conn.execute(
        "SELECT * FROM insights WHERE firm_id = ? ORDER BY CASE status WHEN 'new' THEN 0 WHEN 'accepted' THEN 1 WHEN 'implemented' THEN 2 ELSE 3 END, id",
        (firm["id"],)).fetchall()]
    opps = []
    for o in conn.execute("SELECT * FROM opportunities WHERE firm_id = ? ORDER BY created_at DESC", (firm["id"],)).fetchall():
        d = services.opportunity_dict(o, firm)
        counts = conn.execute(
            "SELECT status, COUNT(*) AS n FROM applications WHERE opportunity_id = ? GROUP BY status", (o["id"],)).fetchall()
        d["applicant_counts"] = {c["status"]: c["n"] for c in counts}
        d["applicant_total"] = sum(c["n"] for c in counts if c["status"] != "withdrawn")
        opps.append(d)
    last = metrics[-1] if metrics else None
    prev3 = metrics[-4:-1]
    kpis = None
    if last and prev3:
        avg_prev = sum(m["revenue"] for m in prev3) / len(prev3)
        kpis = {
            "month": last["month"], "revenue": last["revenue"], "customers": last["customers"],
            "revenue_vs_prev3_pct": round((last["revenue"] - avg_prev) / avg_prev * 100, 1),
            "implemented_count": sum(1 for i in insights if i["status"] == "implemented"),
            "open_roles": sum(1 for o in opps if o["status"] == "published"),
            "new_applicants": sum(o["applicant_counts"].get("submitted", 0) for o in opps),
        }
    f = dict(firm)
    return {
        "firm": {**{k: f[k] for k in ("id", "name", "company_number", "sector", "town", "postcode", "employees", "incorporated", "description")},
                 "sic_codes": loads(f["sic_codes"]), "profile": loads(f["profile"], {})},
        "companies_house": companies_house.company_profile(conn, f["company_number"]),
        "companies_house_mode": companies_house.mode(),
        "metrics": metrics, "impact": _impact(metrics, insights), "kpis": kpis,
        "insights": insights, "opportunities": opps, "ai_mode": owner_agent.ai_mode(),
        "rules": {"minimum_rate": wages.NLW_APRIL_2026, "max_part_time_hours": wages.STUDENT_VISA_TERM_HOURS},
    }


@router.post("/insights/refresh")
def refresh_insights(user: dict = Depends(owner), conn: sqlite3.Connection = Depends(get_db)):
    firm = _firm(conn, user)
    source, items = owner_agent.generate_insights(conn, firm)
    return {"source": source, "count": len(items)}


class InsightStatusIn(BaseModel):
    status: Literal["new", "accepted", "dismissed", "implemented"]


@router.patch("/insights/{insight_id}")
def set_insight_status(insight_id: int, body: InsightStatusIn, user: dict = Depends(owner), conn: sqlite3.Connection = Depends(get_db)):
    firm = _firm(conn, user)
    found = conn.execute("SELECT * FROM insights WHERE id = ? AND firm_id = ?", (insight_id, firm["id"])).fetchone()
    if not found:
        raise HTTPException(404, "Insight not found")
    implemented_at = None
    if body.status == "implemented":
        latest = conn.execute("SELECT MAX(month) FROM firm_metrics WHERE firm_id = ?", (firm["id"],)).fetchone()[0]
        implemented_at = latest
    conn.execute("UPDATE insights SET status = ?, implemented_at = COALESCE(?, implemented_at) WHERE id = ?",
                 (body.status, implemented_at, insight_id))
    return {"ok": True}


@router.post("/insights/{insight_id}/draft")
def draft_from_insight(insight_id: int, user: dict = Depends(owner), conn: sqlite3.Connection = Depends(get_db)):
    firm = _firm(conn, user)
    insight = conn.execute("SELECT * FROM insights WHERE id = ? AND firm_id = ?", (insight_id, firm["id"])).fetchone()
    if not insight:
        raise HTTPException(404, "Insight not found")
    result = owner_agent.draft_from_insight(conn, firm, insight)
    result["insight_id"] = insight_id
    return result


class AdvisorIn(BaseModel):
    prompt: str = Field(min_length=10, max_length=4000)


@router.post("/advisor")
def advisor(body: AdvisorIn, user: dict = Depends(owner), conn: sqlite3.Connection = Depends(get_db)):
    firm = _firm(conn, user)
    return owner_agent.advise(conn, firm, body.prompt)


class WageIn(BaseModel):
    type: Literal["paid_project", "part_time", "internship", "first_job"]
    hourly_rate: float = Field(ge=0, le=200)
    hours_per_week: int = Field(ge=1, le=60)
    weeks: int | None = Field(default=None, ge=0, le=52)


@router.post("/wage-estimate")
def wage_estimate(body: WageIn, user: dict = Depends(owner)):
    weeks = None if body.type == "first_job" else body.weeks
    return {
        "cost": wages.cost_breakdown(body.hourly_rate, body.hours_per_week, weeks, body.type),
        "problems": wages.validate_opportunity(body.type, body.hourly_rate, body.hours_per_week, weeks),
    }


class OpportunityIn(BaseModel):
    title: str = Field(min_length=3, max_length=140)
    type: Literal["paid_project", "part_time", "internship", "first_job"]
    summary: str = Field(min_length=10, max_length=2000)
    tasks: list[str] = Field(default_factory=list, max_length=15)
    plan: list[PlanStep] = Field(default_factory=list, max_length=10)
    skills_required: list[str] = Field(default_factory=list, max_length=12)
    skills_nice: list[str] = Field(default_factory=list, max_length=12)
    removed_requirements: list[str] = Field(default_factory=list, max_length=10)
    success_measures: list[str] = Field(default_factory=list, max_length=10)
    hours_per_week: int
    weeks: int | None = None
    hourly_rate: float
    role_question: str = Field(min_length=10, max_length=500)
    reasoning: str = Field(default="", max_length=3000)
    remote_friendly: bool = False
    insight_id: int | None = None
    source: Literal["claude", "offline", "manual"] = "manual"


@router.post("/opportunities")
def publish_opportunity(body: OpportunityIn, user: dict = Depends(owner), conn: sqlite3.Connection = Depends(get_db)):
    firm = _firm(conn, user)
    weeks = None if body.type == "first_job" else body.weeks
    problems = wages.validate_opportunity(body.type, body.hourly_rate, body.hours_per_week, weeks)
    if problems:
        raise HTTPException(422, " ".join(problems))
    cur = conn.execute(
        """INSERT INTO opportunities (firm_id, insight_id, title, type, summary, tasks, plan, skills_required, skills_nice,
               removed_requirements, success_measures, hours_per_week, weeks, hourly_rate, role_question, ai_reasoning,
               remote_friendly, visibility, status, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'internal', 'published', ?)""",
        (firm["id"], body.insight_id, body.title, body.type, body.summary, dumps(body.tasks),
         dumps([p.model_dump() for p in body.plan]), dumps(body.skills_required), dumps(body.skills_nice),
         dumps(body.removed_requirements), dumps(body.success_measures), body.hours_per_week, weeks,
         round(body.hourly_rate, 2), body.role_question, body.reasoning, int(body.remote_friendly), body.source),
    )
    if body.insight_id:
        conn.execute("UPDATE insights SET status = 'accepted', opportunity_id = ? WHERE id = ? AND firm_id = ?",
                     (cur.lastrowid, body.insight_id, firm["id"]))
    return {"ok": True, "opportunity_id": cur.lastrowid,
            "cost": wages.cost_breakdown(body.hourly_rate, body.hours_per_week, weeks, body.type)}


class OpportunityStatusIn(BaseModel):
    status: Literal["published", "closed"]


@router.patch("/opportunities/{opportunity_id}")
def set_opportunity_status(opportunity_id: int, body: OpportunityStatusIn, user: dict = Depends(owner), conn: sqlite3.Connection = Depends(get_db)):
    firm = _firm(conn, user)
    cur = conn.execute("UPDATE opportunities SET status = ? WHERE id = ? AND firm_id = ?", (body.status, opportunity_id, firm["id"]))
    if not cur.rowcount:
        raise HTTPException(404, "Opportunity not found")
    return {"ok": True}


def _candidate_code(application_id: int) -> str:
    return "Candidate " + hashlib.sha256(f"fh-{application_id}".encode()).hexdigest()[:4].upper()


@router.get("/applicants")
def applicants(opportunity_id: int | None = None, user: dict = Depends(owner), conn: sqlite3.Connection = Depends(get_db)):
    firm = _firm(conn, user)
    sql = """SELECT a.*, o.title AS opp_title, o.type AS opp_type, o.role_question, s.degree, s.grad_year, s.skills,
                    s.experiences, s.hours_per_week AS s_hours, s.availability, s.home_town, s.full_name, s.email,
                    s.phone, s.university, s.on_student_visa
             FROM applications a JOIN opportunities o ON o.id = a.opportunity_id JOIN students s ON s.id = a.student_id
             WHERE o.firm_id = ? AND a.status != 'withdrawn'"""
    params: list = [firm["id"]]
    if opportunity_id:
        sql += " AND o.id = ?"
        params.append(opportunity_id)
    sql += " ORDER BY a.created_at"   # first come, first reviewed — no AI ranking
    out = []
    for a in conn.execute(sql, params).fetchall():
        revealed = a["status"] in services.IDENTITY_VISIBLE
        opp_skills = [x.lower() for x in loads(conn.execute(
            "SELECT skills_required FROM opportunities WHERE id = ?", (a["opportunity_id"],)).fetchone()[0])]
        skills = loads(a["skills"])
        out.append({
            "id": a["id"], "code": _candidate_code(a["id"]), "status": a["status"], "answer": a["answer"],
            "owner_note": a["owner_note"], "interview_at": a["interview_at"], "created_at": a["created_at"],
            "opportunity": {"id": a["opportunity_id"], "title": a["opp_title"], "type": a["opp_type"], "role_question": a["role_question"]},
            "evidence": {
                "degree_subject": a["degree"], "graduation_year": a["grad_year"], "skills": skills,
                "skills_matching_role": [s for s in skills if any(s.lower() in r or r in s.lower() for r in opp_skills)],
                "experiences": [{k: e.get(k, "") for k in ("title", "period", "summary")} for e in loads(a["experiences"])],
                "hours_available": a["s_hours"], "availability": a["availability"],
                "distance_miles": geo.miles_between(a["home_town"], firm["town"]),
                "term_time_limit": 20 if a["on_student_visa"] else None,
            },
            "identity": {"name": a["full_name"], "email": a["email"], "phone": a["phone"], "university": a["university"]} if revealed else None,
        })
    return {"applicants": out, "blind_review": True,
            "note": "Names, photos, universities and contact details are hidden until you invite someone to interview. Applicants are listed in the order they applied — FirstHire's AI never ranks people."}


class DecisionIn(BaseModel):
    action: Literal["shortlist", "interview", "offer", "reject"]
    note: str = Field(default="", max_length=1000)
    interview_at: str | None = Field(default=None, max_length=40)


_ACTION_STATUS = {"shortlist": "shortlisted", "interview": "interview", "offer": "offered", "reject": "rejected"}
_EVENT_NOTE = {
    "shortlisted": "Shortlisted — the firm liked your answer and wants a closer look.",
    "interview": "Invited to interview. The firm can now see your name and contact details.",
    "offered": "Offer made! The firm will contact you with the contract details.",
    "rejected": "Not progressed this time.",
}


@router.post("/applications/{application_id}/decision")
def decide(application_id: int, body: DecisionIn, user: dict = Depends(owner), conn: sqlite3.Connection = Depends(get_db)):
    firm = _firm(conn, user)
    a = conn.execute(
        """SELECT a.*, s.user_id AS student_user_id FROM applications a JOIN opportunities o ON o.id = a.opportunity_id
           JOIN students s ON s.id = a.student_id WHERE a.id = ? AND o.firm_id = ?""",
        (application_id, firm["id"]),
    ).fetchone()
    if not a:
        raise HTTPException(404, "Application not found")
    if a["status"] in services.FINAL_STATUSES:
        raise HTTPException(409, f"This application is already {a['status']}")
    new_status = _ACTION_STATUS[body.action]
    if new_status == "rejected" and not body.note.strip():
        body.note = "Thank you for applying. We had strong interest and chose another applicant this time."
    conn.execute(
        "UPDATE applications SET status=?, owner_note=?, interview_at=COALESCE(?, interview_at), updated_at=datetime('now') WHERE id=?",
        (new_status, body.note.strip(), body.interview_at, application_id),
    )
    note = _EVENT_NOTE[new_status] + (f" Message from the firm: “{body.note.strip()}”" if body.note.strip() else "")
    if body.interview_at:
        note += f" Proposed time: {body.interview_at}."
    services.add_event(conn, application_id, new_status, note)
    if new_status == "interview":
        log_access(conn, a["student_user_id"], firm["name"], "Name and contact details revealed", "Because they invited you to interview")
    else:
        log_access(conn, a["student_user_id"], firm["name"], f"Updated your application: {new_status}")
    return {"ok": True, "status": new_status}
