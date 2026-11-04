"""SQLite storage. One file, zero setup — perfect for a prototype.

JSON-shaped columns are stored as TEXT and decoded with `loads()`.
"""

import json
import sqlite3
from collections.abc import Iterator
from typing import Any

from .config import settings

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('graduate', 'owner')),
    display_name  TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL
);

-- The student "Passport". user_id is NULL for synthetic applicants without a login.
CREATE TABLE IF NOT EXISTS students (
    id                 INTEGER PRIMARY KEY,
    user_id            INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    full_name          TEXT NOT NULL,
    email              TEXT,
    phone              TEXT,
    headline           TEXT DEFAULT '',
    degree             TEXT DEFAULT '',
    university         TEXT DEFAULT '',
    grad_year          INTEGER,
    home_town          TEXT DEFAULT 'Newcastle upon Tyne',
    max_travel_miles   INTEGER DEFAULT 15,
    hours_per_week     INTEGER DEFAULT 20,
    availability       TEXT DEFAULT '',
    on_student_visa    INTEGER DEFAULT 0,
    skills             TEXT DEFAULT '[]',
    experiences        TEXT DEFAULT '[]',
    interests          TEXT DEFAULT '[]',
    cv_text            TEXT DEFAULT '',
    consent_ai         INTEGER DEFAULT 1,
    updated_at         TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS firms (
    id             INTEGER PRIMARY KEY,
    owner_user_id  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    name           TEXT NOT NULL,
    company_number TEXT,
    sic_codes      TEXT DEFAULT '[]',
    sector         TEXT,
    town           TEXT,
    postcode       TEXT,
    employees      INTEGER,
    incorporated   TEXT,
    description    TEXT,
    profile        TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS firm_metrics (
    firm_id   INTEGER NOT NULL REFERENCES firms(id) ON DELETE CASCADE,
    month     TEXT NOT NULL,          -- YYYY-MM
    revenue   REAL NOT NULL,
    customers INTEGER NOT NULL,
    PRIMARY KEY (firm_id, month)
);

CREATE TABLE IF NOT EXISTS insights (
    id               INTEGER PRIMARY KEY,
    firm_id          INTEGER NOT NULL REFERENCES firms(id) ON DELETE CASCADE,
    category         TEXT,
    title            TEXT NOT NULL,
    problem          TEXT,
    recommendation   TEXT,
    expected_impact  TEXT,
    effort           TEXT,
    evidence         TEXT,
    opportunity_type TEXT,
    role_title       TEXT,
    status           TEXT NOT NULL DEFAULT 'new',   -- new | accepted | dismissed | implemented
    source           TEXT NOT NULL DEFAULT 'seed',  -- seed | claude | offline
    opportunity_id   INTEGER,
    implemented_at   TEXT,                          -- YYYY-MM
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS opportunities (
    id                   INTEGER PRIMARY KEY,
    firm_id              INTEGER NOT NULL REFERENCES firms(id) ON DELETE CASCADE,
    insight_id           INTEGER,
    title                TEXT NOT NULL,
    type                 TEXT NOT NULL CHECK (type IN ('paid_project', 'part_time', 'internship', 'first_job')),
    summary              TEXT,
    tasks                TEXT DEFAULT '[]',
    plan                 TEXT DEFAULT '[]',
    skills_required      TEXT DEFAULT '[]',
    skills_nice          TEXT DEFAULT '[]',
    removed_requirements TEXT DEFAULT '[]',
    success_measures     TEXT DEFAULT '[]',
    hours_per_week       INTEGER NOT NULL,
    weeks                INTEGER,
    hourly_rate          REAL NOT NULL,
    role_question        TEXT NOT NULL,
    ai_reasoning         TEXT DEFAULT '',
    remote_friendly      INTEGER DEFAULT 0,
    visibility           TEXT NOT NULL DEFAULT 'internal',
    status               TEXT NOT NULL DEFAULT 'published',  -- draft | published | closed
    source               TEXT NOT NULL DEFAULT 'seed',
    created_at           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS applications (
    id             INTEGER PRIMARY KEY,
    opportunity_id INTEGER NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    student_id     INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    answer         TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'submitted',
    owner_note     TEXT DEFAULT '',
    interview_at   TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (opportunity_id, student_id)
);

CREATE TABLE IF NOT EXISTS application_events (
    id             INTEGER PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    status         TEXT NOT NULL,
    note           TEXT DEFAULT '',
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS passes (
    student_id     INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    opportunity_id INTEGER NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    PRIMARY KEY (student_id, opportunity_id)
);

CREATE TABLE IF NOT EXISTS match_cache (
    student_id INTEGER PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE,
    input_hash TEXT NOT NULL,
    result     TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Transparency log: every time someone or something touches a user's data.
CREATE TABLE IF NOT EXISTS access_log (
    id              INTEGER PRIMARY KEY,
    subject_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    actor           TEXT NOT NULL,
    action          TEXT NOT NULL,
    detail          TEXT DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def connect() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request, committed on success."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def loads(value: str | None, default: Any = None) -> Any:
    if value in (None, ""):
        return [] if default is None else default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return [] if default is None else default


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def row(r: sqlite3.Row | None) -> dict | None:
    return dict(r) if r is not None else None


def log_access(conn: sqlite3.Connection, subject_user_id: int | None, actor: str, action: str, detail: str = "") -> None:
    if subject_user_id is None:
        return
    conn.execute(
        "INSERT INTO access_log (subject_user_id, actor, action, detail) VALUES (?, ?, ?, ?)",
        (subject_user_id, actor, action, detail),
    )
