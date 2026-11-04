import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from ..db import get_db
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
