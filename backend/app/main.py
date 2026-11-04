"""FirstHire API — run with:  uvicorn app.main:app --reload --port 8000  (from /backend)"""

import logging
import sqlite3

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from . import companies_house, geo
from .config import settings
from .db import connect, get_db, init_db
from .routers import account, auth, owner, student
from .security import current_user

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="FirstHire API", version="0.1.0", docs_url="/api/docs", openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/docs"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.on_event("startup")
def _startup() -> None:
    init_db()
    with connect() as conn:
        empty = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
    if empty:  # first run: create the synthetic demo data automatically
        from .seed import seed

        seed()


app.include_router(auth.router)
app.include_router(student.router)
app.include_router(owner.router)
app.include_router(account.router)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "ai_mode": "claude" if settings.ai_enabled else "offline",
        "model": settings.claude_model if settings.ai_enabled else None,
        "companies_house": companies_house.mode(),
    }


@app.get("/api/public/stats")
def public_stats(conn: sqlite3.Connection = Depends(get_db)):
    q = lambda sql: conn.execute(sql).fetchone()[0]  # noqa: E731
    return {
        "firms": q("SELECT COUNT(*) FROM firms"),
        "open_opportunities": q("SELECT COUNT(*) FROM opportunities WHERE status = 'published'"),
        "towns": q("SELECT COUNT(DISTINCT town) FROM firms"),
        "graduates": q("SELECT COUNT(*) FROM students"),
    }


@app.get("/api/towns")
def towns():
    return {"region": geo.REGION, "towns": geo.town_names()}


@app.get("/api/companies/search")
def companies_search(
    location: str = Query(min_length=2, max_length=80),
    sic: str | None = Query(default=None, description="Comma-separated SIC codes"),
    _: dict = Depends(current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    codes = [c.strip() for c in sic.split(",")] if sic else None
    return companies_house.search_local(conn, location, codes)
