from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, Request, Response
from jose import JWTError, jwt

from .config import settings

COOKIE_NAME = "portal_token"
ALGORITHM = "HS256"
TOKEN_TTL_HOURS = 8


def create_access_token(payload: dict[str, Any]) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)
    to_encode = {**payload, "exp": exp}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def set_auth_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=TOKEN_TTL_HOURS * 3600,
        path="/",
    )


def clear_auth_cookie(resp: Response) -> None:
    resp.delete_cookie(key=COOKIE_NAME, path="/")


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail={"detail": "Unauthorized", "code": "auth.unauthorized"})


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError as e:
        raise _unauthorized() from e


async def require_auth(request: Request) -> dict[str, Any]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise _unauthorized()
    return decode_token(token)

