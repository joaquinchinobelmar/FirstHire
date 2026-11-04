import io
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .. import geo, services
from ..ai import student_agent
from ..ai.privacy import anonymised_passport
from ..config import settings
from ..db import dumps, get_db, loads
from ..security import require_role

router = APIRouter(prefix="/api/student", tags=["graduate"])
graduate = require_role("graduate")


def _student(conn: sqlite3.Connection, user: dict) -> dict:
    s = services.student_for_user(conn, user["id"])
    if not s:
        raise HTTPException(404, "Passport not found")
    return dict(s)


def _passport_out(s: dict) -> dict:
    return {
        **{k: s[k] for k in ("full_name", "email", "phone", "headline", "degree", "university", "grad_year",
                              "home_town", "max_travel_miles", "hours_per_week", "availability", "cv_text", "updated_at")},
        "on_student_visa": bool(s["on_student_visa"]),
        "consent_ai": bool(s["consent_ai"]),
        "skills": loads(s["skills"]),
        "experiences": loads(s["experiences"]),
        "interests": loads(s["interests"]),
        "ai_preview": anonymised_passport(s),
        "towns": geo.town_names(),
    }


class ExperienceIn(BaseModel):
    title: str = Field(max_length=120)
    organisation: str = Field(default="", max_length=120)
    period: str = Field(default="", max_length=60)
    summary: str = Field(default="", max_length=600)


class PassportIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(default="", max_length=40)
    headline: str = Field(default="", max_length=160)
    degree: str = Field(default="", max_length=160)
    university: str = Field(default="", max_length=160)
    grad_year: int | None = Field(default=None, ge=1990, le=2035)
    home_town: str
    max_travel_miles: int = Field(ge=1, le=60)
    hours_per_week: int = Field(ge=4, le=48)
    availability: str = Field(default="", max_length=300)
    on_student_visa: bool = False
    consent_ai: bool = True
    skills: list[str] = Field(default_factory=list, max_length=40)
    experiences: list[ExperienceIn] = Field(default_factory=list, max_length=15)
    interests: list[str] = Field(default_factory=list, max_length=15)
    cv_text: str = Field(default="", max_length=30000)


@router.get("/passport")
def get_passport(user: dict = Depends(graduate), conn: sqlite3.Connection = Depends(get_db)):
    return _passport_out(_student(conn, user))


@router.put("/passport")
def save_passport(body: PassportIn, user: dict = Depends(graduate), conn: sqlite3.Connection = Depends(get_db)):
    s = _student(conn, user)
    if not geo.is_in_region(body.home_town):
        raise HTTPException(422, "FirstHire currently covers North East England only.")
    skills = sorted({x.strip() for x in body.skills if x.strip()}, key=str.lower)
    conn.execute(
        """UPDATE students SET full_name=?, phone=?, headline=?, degree=?, university=?, grad_year=?, home_town=?,
               max_travel_miles=?, hours_per_week=?, availability=?, on_student_visa=?, consent_ai=?, skills=?,
               experiences=?, interests=?, cv_text=?, updated_at=datetime('now') WHERE id=?""",
        (body.full_name, body.phone, body.headline, body.degree, body.university, body.grad_year, body.home_town,
         body.max_travel_miles, body.hours_per_week, body.availability, int(body.on_student_visa), int(body.consent_ai),
         dumps(skills), dumps([e.model_dump() for e in body.experiences]), dumps(body.interests), body.cv_text, s["id"]),
    )
    return _passport_out(_student(conn, user))


@router.post("/passport/cv")
async def upload_cv(file: UploadFile = File(...), user: dict = Depends(graduate), conn: sqlite3.Connection = Depends(get_db)):
    s = _student(conn, user)
    raw = await file.read()
    if len(raw) > 3 * 1024 * 1024:
        raise HTTPException(413, "CV must be under 3 MB")
    name = (file.filename or "").lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        try:
            text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages[:6])
        except Exception:
            raise HTTPException(422, "Couldn't read that PDF. Try exporting it again or paste the text instead.")
    elif name.endswith((".txt", ".md")):
        text = raw.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(415, "Upload a PDF or .txt file")
    text = text.strip()[:30000]
    conn.execute("UPDATE students SET cv_text=?, updated_at=datetime('now') WHERE id=?", (text, s["id"]))
    # The original file is not stored — only the extracted text the graduate can see and edit.
    return {"cv_text": text, "draft": student_agent.autofill_from_cv(text, allow_ai=bool(s["consent_ai"]))}


class AutofillIn(BaseModel):
    cv_text: str = Field(min_length=30, max_length=30000)


@router.post("/passport/autofill")
def autofill(body: AutofillIn, user: dict = Depends(graduate), conn: sqlite3.Connection = Depends(get_db)):
    s = _student(conn, user)
    return student_agent.autofill_from_cv(body.cv_text, allow_ai=bool(s["consent_ai"]))


@router.get("/matches")
def matches(refresh: bool = False, user: dict = Depends(graduate), conn: sqlite3.Connection = Depends(get_db)):
    s = _student(conn, user)
    data = student_agent.get_matches(conn, s, user["id"], refresh)
    data["applications_this_month"] = _apps_this_month(conn, s["id"])
    data["monthly_limit"] = settings.monthly_application_limit
    return data


def _apps_this_month(conn: sqlite3.Connection, student_id: int) -> int:
    month = date.today().strftime("%Y-%m")
    return conn.execute(
        "SELECT COUNT(*) FROM applications WHERE student_id = ? AND substr(created_at, 1, 7) = ?", (student_id, month)
    ).fetchone()[0]


class ApplyIn(BaseModel):
    answer: str = Field(max_length=2500)
    confirm_hours: bool = False


@router.post("/opportunities/{opportunity_id}/apply")
def apply(opportunity_id: int, body: ApplyIn, user: dict = Depends(graduate), conn: sqlite3.Connection = Depends(get_db)):
    s = _student(conn, user)
    opp = conn.execute("SELECT * FROM opportunities WHERE id = ? AND status = 'published'", (opportunity_id,)).fetchone()
    if not opp:
        raise HTTPException(404, "This opportunity is no longer open")
    if len(body.answer.strip()) < settings.min_answer_chars:
        raise HTTPException(422, f"Please answer the role question in at least {settings.min_answer_chars} characters — it's what the firm reviews first.")
    if s["on_student_visa"] and not body.confirm_hours:
        raise HTTPException(422, "Please confirm these hours fit within your Student-visa limit.")
    if _apps_this_month(conn, s["id"]) >= settings.monthly_application_limit:
        raise HTTPException(429, f"You've reached this month's limit of {settings.monthly_application_limit} applications. Quality beats quantity — small firms review every one by hand.")
    if conn.execute("SELECT 1 FROM applications WHERE opportunity_id=? AND student_id=?", (opportunity_id, s["id"])).fetchone():
        raise HTTPException(409, "You've already applied to this opportunity")
    cur = conn.execute(
        "INSERT INTO applications (opportunity_id, student_id, answer) VALUES (?, ?, ?)",
        (opportunity_id, s["id"], body.answer.strip()),
    )
    services.add_event(conn, cur.lastrowid, "submitted", "Application sent. The firm sees your answer and skills first — not your name or university.")
    return {"ok": True, "application_id": cur.lastrowid}


@router.post("/opportunities/{opportunity_id}/pass")
def pass_opportunity(opportunity_id: int, user: dict = Depends(graduate), conn: sqlite3.Connection = Depends(get_db)):
    s = _student(conn, user)
    conn.execute("INSERT OR IGNORE INTO passes (student_id, opportunity_id) VALUES (?, ?)", (s["id"], opportunity_id))
    return {"ok": True}


@router.delete("/passes")
def reset_passes(user: dict = Depends(graduate), conn: sqlite3.Connection = Depends(get_db)):
    s = _student(conn, user)
    conn.execute("DELETE FROM passes WHERE student_id = ?", (s["id"],))
    return {"ok": True}


@router.get("/applications")
def applications(user: dict = Depends(graduate), conn: sqlite3.Connection = Depends(get_db)):
    s = _student(conn, user)
    rows = conn.execute(
        """SELECT a.*, o.id AS o_id FROM applications a JOIN opportunities o ON o.id = a.opportunity_id
           WHERE a.student_id = ? ORDER BY a.updated_at DESC""",
        (s["id"],),
    ).fetchall()
    out = []
    for a in rows:
        opp = conn.execute("SELECT * FROM opportunities WHERE id = ?", (a["opportunity_id"],)).fetchone()
        firm = services.firm_by_id(conn, opp["firm_id"])
        events = conn.execute(
            "SELECT status, note, created_at FROM application_events WHERE application_id = ? ORDER BY created_at, id", (a["id"],)
        ).fetchall()
        out.append({
            "id": a["id"], "status": a["status"], "answer": a["answer"], "owner_note": a["owner_note"],
            "interview_at": a["interview_at"], "created_at": a["created_at"], "updated_at": a["updated_at"],
            "opportunity": services.opportunity_dict(opp, firm, s["home_town"]),
            "events": [dict(e) for e in events],
        })
    return {"applications": out, "flow": services.APPLICATION_FLOW,
            "applications_this_month": _apps_this_month(conn, s["id"]), "monthly_limit": settings.monthly_application_limit}


@router.post("/applications/{application_id}/withdraw")
def withdraw(application_id: int, user: dict = Depends(graduate), conn: sqlite3.Connection = Depends(get_db)):
    s = _student(conn, user)
    a = conn.execute("SELECT * FROM applications WHERE id = ? AND student_id = ?", (application_id, s["id"])).fetchone()
    if not a:
        raise HTTPException(404, "Application not found")
    if a["status"] in services.FINAL_STATUSES:
        raise HTTPException(409, "This application is already closed")
    conn.execute("UPDATE applications SET status='withdrawn', updated_at=datetime('now') WHERE id=?", (application_id,))
    services.add_event(conn, application_id, "withdrawn", "You withdrew this application.")
    return {"ok": True}
