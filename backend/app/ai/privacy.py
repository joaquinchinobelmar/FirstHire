"""Data minimisation: what each AI agent is allowed to see.

The graduate agent never sees name, email, phone, photo or university.
Contact details are scrubbed from free text (CVs) before any AI call.
"""

import re

from ..db import loads

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(\+?44\s?|0)(\d[\s-]?){9,10}")
_URL = re.compile(r"https?://\S+|www\.\S+|linkedin\.com/\S+", re.IGNORECASE)
_POSTCODE = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b", re.IGNORECASE)


def redact(text: str) -> str:
    text = _EMAIL.sub("[email removed]", text or "")
    text = _URL.sub("[link removed]", text)
    text = _PHONE.sub("[phone removed]", text)
    text = _POSTCODE.sub("[postcode removed]", text)
    return text


def anonymised_passport(student: dict) -> dict:
    """Exactly what the matching agent receives. Shown to the graduate in the UI."""
    experiences = [
        {k: redact(str(e.get(k, ""))) for k in ("title", "organisation", "period", "summary")}
        for e in loads(student.get("experiences"))
    ]
    return {
        "degree": student.get("degree") or "",
        "graduation_year": student.get("grad_year"),
        "headline": redact(student.get("headline") or ""),
        "skills": loads(student.get("skills")),
        "experiences": experiences,
        "interests": loads(student.get("interests")),
        "hours_available_per_week": student.get("hours_per_week"),
        "availability": redact(student.get("availability") or ""),
        "home_area": student.get("home_town"),
        "max_travel_miles": student.get("max_travel_miles"),
        "term_time_hour_limit": 20 if student.get("on_student_visa") else None,
        "_removed_before_ai": ["name", "email", "phone", "photo", "university", "contact details inside CV"],
    }
