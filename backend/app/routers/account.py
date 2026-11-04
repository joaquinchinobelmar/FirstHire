"""Trust & privacy: every user can see, export and delete their own data."""

import sqlite3

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from .. import services
from ..ai.privacy import anonymised_passport
from ..db import get_db, loads
from ..security import current_user, destroy_session

router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("/access-log")
def access_log(user: dict = Depends(current_user), conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute(
        "SELECT actor, action, detail, created_at FROM access_log WHERE subject_user_id = ? ORDER BY created_at DESC, id DESC LIMIT 100",
        (user["id"],),
    ).fetchall()
    return {"entries": [dict(r) for r in rows]}


@router.get("/export")
def export(user: dict = Depends(current_user), conn: sqlite3.Connection = Depends(get_db)):
    data: dict = {"account": {k: user[k] for k in ("email", "role", "name")}}
    if user["role"] == "graduate":
        s = services.student_for_user(conn, user["id"])
        if s:
            s = dict(s)
            for k in ("skills", "experiences", "interests"):
                s[k] = loads(s[k])
            data["passport"] = s
            data["what_ai_sees"] = anonymised_passport(dict(services.student_for_user(conn, user["id"])))
            data["applications"] = [dict(a) for a in conn.execute(
                "SELECT a.status, a.answer, a.created_at, o.title FROM applications a JOIN opportunities o ON o.id = a.opportunity_id WHERE a.student_id = ?",
                (s["id"],)).fetchall()]
    else:
        f = services.firm_for_owner(conn, user["id"])
        if f:
            data["firm"] = dict(f)
            data["opportunities"] = [dict(o) for o in conn.execute("SELECT * FROM opportunities WHERE firm_id = ?", (f["id"],)).fetchall()]
            data["insights"] = [dict(i) for i in conn.execute("SELECT * FROM insights WHERE firm_id = ?", (f["id"],)).fetchall()]
    data["access_log"] = [dict(r) for r in conn.execute(
        "SELECT actor, action, detail, created_at FROM access_log WHERE subject_user_id = ?", (user["id"],)).fetchall()]
    return JSONResponse(data, headers={"Content-Disposition": 'attachment; filename="firsthire-my-data.json"'})


@router.delete("")
def delete_account(request: Request, response: Response, user: dict = Depends(current_user), conn: sqlite3.Connection = Depends(get_db)):
    destroy_session(conn, request, response)
    conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))   # cascades to passport, applications, sessions, log
    return {"ok": True, "message": "Your account and personal data have been deleted."}
