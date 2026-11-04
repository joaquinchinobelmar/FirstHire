"""Shared helpers: serialising rows for the API and small domain queries."""

import sqlite3

from . import geo, wages
from .db import loads

APPLICATION_FLOW = ["submitted", "shortlisted", "interview", "offered"]
FINAL_STATUSES = {"offered", "rejected", "withdrawn"}
IDENTITY_VISIBLE = {"interview", "offered"}   # name + contact revealed to firm only from here


def opportunity_dict(opp: sqlite3.Row | dict, firm: sqlite3.Row | dict, home_town: str | None = None) -> dict:
    opp, firm = dict(opp), dict(firm)
    distance = geo.miles_between(home_town, firm["town"]) if home_town else None
    return {
        "id": opp["id"],
        "title": opp["title"],
        "type": opp["type"],
        "type_label": wages.TYPE_LABELS.get(opp["type"], opp["type"]),
        "summary": opp["summary"],
        "tasks": loads(opp["tasks"]),
        "plan": loads(opp["plan"]),
        "skills_required": loads(opp["skills_required"]),
        "skills_nice": loads(opp["skills_nice"]),
        "removed_requirements": loads(opp["removed_requirements"]),
        "success_measures": loads(opp["success_measures"]),
        "hours_per_week": opp["hours_per_week"],
        "weeks": opp["weeks"],
        "hourly_rate": opp["hourly_rate"],
        "cost": wages.cost_breakdown(opp["hourly_rate"], opp["hours_per_week"], opp["weeks"], opp["type"]),
        "role_question": opp["role_question"],
        "ai_reasoning": opp["ai_reasoning"],
        "remote_friendly": bool(opp["remote_friendly"]),
        "visibility": opp["visibility"],
        "status": opp["status"],
        "source": opp["source"],
        "insight_id": opp["insight_id"],
        "created_at": opp["created_at"],
        "distance_miles": distance,
        "firm": {
            "id": firm["id"],
            "name": firm["name"],
            "sector": firm["sector"],
            "town": firm["town"],
            "employees": firm["employees"],
            "description": firm["description"],
        },
    }


def get_opportunity_with_firm(conn: sqlite3.Connection, opportunity_id: int):
    return conn.execute(
        """SELECT o.*, f.id AS f_id FROM opportunities o JOIN firms f ON f.id = o.firm_id WHERE o.id = ?""",
        (opportunity_id,),
    ).fetchone()


def firm_by_id(conn: sqlite3.Connection, firm_id: int):
    return conn.execute("SELECT * FROM firms WHERE id = ?", (firm_id,)).fetchone()


def add_event(conn: sqlite3.Connection, application_id: int, status: str, note: str = "") -> None:
    conn.execute(
        "INSERT INTO application_events (application_id, status, note) VALUES (?, ?, ?)",
        (application_id, status, note),
    )


def student_for_user(conn: sqlite3.Connection, user_id: int):
    return conn.execute("SELECT * FROM students WHERE user_id = ?", (user_id,)).fetchone()


def firm_for_owner(conn: sqlite3.Connection, user_id: int):
    return conn.execute("SELECT * FROM firms WHERE owner_user_id = ?", (user_id,)).fetchone()
