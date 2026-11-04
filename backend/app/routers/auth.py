import hmac
import secrets
import sqlite3
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from .. import linkedin
from ..config import settings
from ..db import get_db, log_access
from ..security import (
    check_login_rate,
    clear_login_attempts,
    create_session,
    current_user,
    destroy_session,
    hash_password,
    record_failed_login,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
_DUMMY_HASH = hash_password("timing-equaliser")


class LoginIn(BaseModel):
    email: str = Field(max_length=200)
    password: str = Field(max_length=200)


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response, conn: sqlite3.Connection = Depends(get_db)):
    email = body.email.strip().lower()
    key = f"{email}|{request.client.host if request.client else '?'}"
    check_login_rate(key)
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    ok = verify_password(body.password, user["password_hash"] if user else _DUMMY_HASH)
    if not user or not ok:
        record_failed_login(key)
        raise HTTPException(401, "Incorrect email or password")
    clear_login_attempts(key)
    create_session(conn, user["id"], response)
    return {"id": user["id"], "name": user["display_name"], "role": user["role"], "email": user["email"]}


@router.post("/logout")
def logout(request: Request, response: Response, conn: sqlite3.Connection = Depends(get_db)):
    destroy_session(conn, request, response)
    return {"ok": True}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return user


# ---------------- Sign in / sign up with LinkedIn (graduates only) ----------------
STATE_COOKIE = "fh_oauth_state"


def _login_error(message: str) -> RedirectResponse:
    resp = RedirectResponse(f"/login?as=graduate&error={urllib.parse.quote(message)}", status_code=303)
    resp.delete_cookie(STATE_COOKIE, path="/")
    return resp


@router.get("/providers")
def providers():
    return {"linkedin": settings.linkedin_mode}


@router.get("/linkedin/start")
def linkedin_start():
    state = secrets.token_urlsafe(24)
    target = linkedin.authorize_url(state) if settings.linkedin_mode == "live" else f"/auth/linkedin/demo?state={state}"
    resp = RedirectResponse(target, status_code=303)
    resp.set_cookie(STATE_COOKIE, state, max_age=600, httponly=True, secure=settings.cookie_secure, samesite="lax", path="/")
    return resp


@router.get("/linkedin/callback")
def linkedin_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    conn: sqlite3.Connection = Depends(get_db),
):
    if error:
        return _login_error("LinkedIn sign-in was cancelled.")
    expected = request.cookies.get(STATE_COOKIE)
    if not code or not state or not expected or not hmac.compare_digest(state, expected):
        return _login_error("Your sign-in link expired. Please try again.")
    try:
        profile = linkedin.profile_from_code(code)
    except linkedin.LinkedInError as e:
        return _login_error(str(e))

    user = conn.execute("SELECT * FROM users WHERE linkedin_sub = ?", (profile["sub"],)).fetchone()
    is_new = False
    if not user:
        existing = conn.execute("SELECT * FROM users WHERE email = ?", (profile["email"],)).fetchone()
        if existing:
            if existing["role"] != "graduate":
                return _login_error("LinkedIn sign-in is for graduates. Business accounts sign in with email and password.")
            # Only link to an existing account when LinkedIn has verified the email (never in demo mode)
            if settings.linkedin_mode != "live" or not profile["email_verified"]:
                return _login_error("An account with this email already exists. Sign in with your password.")
            conn.execute("UPDATE users SET linkedin_sub = ? WHERE id = ?", (profile["sub"], existing["id"]))
            user = existing
        else:
            cur = conn.execute(
                "INSERT INTO users (email, password_hash, role, display_name, linkedin_sub) VALUES (?, '!linkedin-only', 'graduate', ?, ?)",
                (profile["email"], profile["name"], profile["sub"]),
            )
            conn.execute(
                "INSERT INTO students (user_id, full_name, email, home_town, consent_ai) VALUES (?, ?, ?, 'Newcastle upon Tyne', 1)",
                (cur.lastrowid, profile["name"], profile["email"]),
            )
            user = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
            is_new = True
            log_access(conn, user["id"], "LinkedIn", "Account created with LinkedIn",
                       "Received: name and email. Not stored: photo or anything else from your LinkedIn profile.")

    if user["role"] != "graduate":
        return _login_error("LinkedIn sign-in is for graduates only.")
    resp = RedirectResponse("/graduate/profile?welcome=linkedin" if is_new else "/graduate/opportunities", status_code=303)
    resp.delete_cookie(STATE_COOKIE, path="/")
    create_session(conn, user["id"], resp)
    return resp
