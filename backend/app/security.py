"""Authentication: salted PBKDF2 password hashes + opaque session tokens in an HttpOnly cookie.

- Passwords are never stored or logged in plain text.
- The browser only ever holds a random token; the DB only stores its SHA-256 hash.
- Login attempts are rate limited per email + IP.
"""

import hashlib
import hmac
import secrets
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, Response, status

from .config import settings
from .db import get_db

COOKIE_NAME = "fh_session"
_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except ValueError:
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(conn: sqlite3.Connection, user_id: int, response: Response) -> None:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.session_ttl_hours)
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
        (_token_hash(token), user_id, expires.isoformat()),
    )
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def destroy_session(conn: sqlite3.Connection, request: Request, response: Response) -> None:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
    response.delete_cookie(COOKIE_NAME, path="/")


def current_user(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    found = conn.execute(
        """SELECT u.id, u.email, u.role, u.display_name, s.expires_at
           FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token_hash = ?""",
        (_token_hash(token),),
    ).fetchone()
    if not found or datetime.fromisoformat(found["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired")
    return {"id": found["id"], "email": found["email"], "role": found["role"], "name": found["display_name"]}


def require_role(role: str):
    def checker(user: dict = Depends(current_user)) -> dict:
        if user["role"] != role:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This area is not available for your account type")
        return user

    return checker


# --- naive in-memory rate limiter (fine for a single-process prototype) ---
_attempts: dict[str, list[float]] = defaultdict(list)
_WINDOW_SECONDS = 300
_MAX_ATTEMPTS = 6


def check_login_rate(key: str) -> None:
    now = time.time()
    recent = [t for t in _attempts[key] if now - t < _WINDOW_SECONDS]
    _attempts[key] = recent
    if len(recent) >= _MAX_ATTEMPTS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Please wait a few minutes.")


def record_failed_login(key: str) -> None:
    _attempts[key].append(time.time())


def clear_login_attempts(key: str) -> None:
    _attempts.pop(key, None)
