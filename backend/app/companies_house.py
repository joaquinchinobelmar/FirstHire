"""Companies House Public Data API client (UK government, free key).

Docs: https://developer-specs.company-information.service.gov.uk/
Auth: HTTP Basic, API key as the username, empty password.

Used for: verifying a firm's registration and building outreach lists of active
local companies by SIC code + location. In the hackathon demo the firms are
synthetic (company numbers start with "SYN"), so without a key — or for
synthetic numbers — we answer from the local snapshot in the same response shape.
"""

import base64
import json
import sqlite3
import urllib.parse
import urllib.request

from .config import settings
from .db import loads

BASE_URL = "https://api.company-information.service.gov.uk"

# Target sectors from the product brief (SIC 2007 codes)
TARGET_SIC = {
    "professional_services": ["69201", "69102", "70229", "71129", "73110", "62020"],
    "manufacturing": ["25620", "10710", "28990"],
    "construction": ["41201", "43210", "43390"],
    "care": ["87300", "88100", "86900"],
    "hospitality_retail": ["56101", "56102", "47190", "47910"],
}


def mode() -> str:
    return "live" if settings.companies_house_key else "snapshot"


def _get(path: str, params: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    token = base64.b64encode(f"{settings.companies_house_key}:".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {token}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode())


def _snapshot_record(firm: dict) -> dict:
    return {
        "company_name": firm["name"].upper(),
        "company_number": firm["company_number"],
        "company_status": "active",
        "company_type": "ltd",
        "date_of_creation": firm["incorporated"],
        "registered_office_address": {"locality": firm["town"], "postal_code": firm["postcode"], "region": "North East"},
        "sic_codes": loads(firm["sic_codes"]),
        "source": "synthetic-snapshot",
    }


def company_profile(conn: sqlite3.Connection, company_number: str) -> dict | None:
    if settings.companies_house_key and not company_number.startswith("SYN"):
        try:
            data = _get(f"/company/{urllib.parse.quote(company_number)}")
            data["source"] = "companies-house-live"
            return data
        except Exception:  # network / 404 / quota — fall back silently
            pass
    firm = conn.execute("SELECT * FROM firms WHERE company_number = ?", (company_number,)).fetchone()
    return _snapshot_record(dict(firm)) if firm else None


def search_local(conn: sqlite3.Connection, location: str, sic_codes: list[str] | None = None, size: int = 20) -> dict:
    """Active companies registered in `location`, optionally filtered by SIC codes."""
    if settings.companies_house_key:
        try:
            params = {"location": location, "company_status": "active", "size": size}
            if sic_codes:
                params["sic_codes"] = ",".join(sic_codes)
            data = _get("/advanced-search/companies", params)
            return {"source": "companies-house-live", "items": data.get("items", [])}
        except Exception:
            pass
    items = []
    for firm in conn.execute("SELECT * FROM firms WHERE town LIKE ?", (f"%{location}%",)).fetchall():
        rec = _snapshot_record(dict(firm))
        if not sic_codes or set(sic_codes) & set(rec["sic_codes"]):
            items.append(rec)
    return {"source": "synthetic-snapshot", "items": items[:size]}
