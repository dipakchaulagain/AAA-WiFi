from __future__ import annotations

import bcrypt
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from ..auth import clear_auth_cookie, create_access_token, set_auth_cookie
from ..database import db_conn
from ..rate_limit import limiter
from ._errors import api_error

router = APIRouter()


class LoginPayload(BaseModel):
    username: str
    password: str


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, resp: Response, payload: LoginPayload):
    async with db_conn() as (_conn, cur):
        await cur.execute(
            "SELECT username, password_hash, role FROM portal_users WHERE username=%s LIMIT 1",
            (payload.username,),
        )
        row = await cur.fetchone()

    if not row:
        raise api_error(401, "auth.invalid_credentials", "Invalid username or password.")

    ok = bcrypt.checkpw(payload.password.encode("utf-8"), row["password_hash"].encode("utf-8"))
    if not ok:
        raise api_error(401, "auth.invalid_credentials", "Invalid username or password.")

    token = create_access_token({"sub": row["username"], "role": row["role"]})
    set_auth_cookie(resp, token)
    return {"success": True}


@router.post("/logout")
async def logout(resp: Response):
    clear_auth_cookie(resp)
    return {"success": True}

