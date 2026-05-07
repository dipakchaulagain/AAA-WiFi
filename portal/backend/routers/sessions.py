from __future__ import annotations

from fastapi import APIRouter, Request

from ..database import db_conn
from ..services.audit import write_audit
from ..services.coa_sender import disconnect_session
from ..services.radius_db import get_active_sessions, get_session_by_id
from ._errors import api_error

router = APIRouter()


@router.get("/active")
async def active():
    return await get_active_sessions()


@router.delete("/{radacctid}")
async def disconnect(radacctid: int, request: Request):
    sess = await get_session_by_id(radacctid)
    if not sess:
        raise api_error(404, "sessions.not_found", "Session not found.")

    nas_ip = sess.get("nasipaddress")
    username = sess.get("username")
    acctsessionid = sess.get("acctsessionid")
    if not (nas_ip and username and acctsessionid):
        raise api_error(400, "sessions.invalid", "Session record missing required attributes.")

    async with db_conn() as (_conn, cur):
        await cur.execute("SELECT secret FROM nas WHERE nasname=%s LIMIT 1", (nas_ip,))
        nas = await cur.fetchone()
    if not nas:
        raise api_error(400, "nas.not_found", "NAS entry not found for this session.")

    ok = disconnect_session(nas_ip=nas_ip, nas_secret=nas["secret"], session_id=acctsessionid, username=username)
    await write_audit(
        admin_user=(request.state.user.get("sub") if hasattr(request.state, "user") else None),
        action="session.disconnect",
        target=str(radacctid),
        detail={"nas_ip": nas_ip, "username": username, "ack": ok},
        ip_address=request.client.host if request.client else None,
    )
    if not ok:
        raise api_error(502, "coa.failed", "Disconnect-Request failed or was not acknowledged by NAS.")
    return {"success": True}

