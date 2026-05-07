from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..config import settings
from ..services.crypto import decrypt_aes_gcm
from ..services.ldap_client import LdapClient, LdapConfig
from ..services.radius_db import get_app_config
from ._errors import api_error

router = APIRouter()


def _aes_key_bytes() -> bytes:
    return bytes.fromhex(settings.AES_KEY)


class TestAuthPayload(BaseModel):
    username: str
    password: str


@router.post("/test-auth")
async def test_auth(payload: TestAuthPayload):
    cfg = await get_app_config(["radius_shared_secret"])
    if not cfg.get("radius_shared_secret"):
        raise api_error(400, "radius.not_configured", "RADIUS shared secret not configured.")
    secret = decrypt_aes_gcm(cfg["radius_shared_secret"], _aes_key_bytes())
    try:
        proc = subprocess.run(
            ["radtest", payload.username, payload.password, "127.0.0.1", "0", secret],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            check=False,
        )
        out = (proc.stdout or b"").decode("utf-8", errors="replace")
        return {"success": proc.returncode == 0 and "Access-Accept" in out, "output": out}
    except subprocess.TimeoutExpired:
        raise api_error(504, "diag.timeout", "radtest timed out.")


@router.post("/test-ldap")
async def test_ldap():
    cfg = await get_app_config(
        ["ldap_server", "ldap_bind_dn", "ldap_bind_pw", "ldap_base_dn", "ldap_group_dn", "ldap_user_filter"]
    )
    if not cfg.get("ldap_server"):
        raise api_error(400, "ldap.not_configured", "LDAP is not configured.")
    bind_pw = decrypt_aes_gcm(cfg.get("ldap_bind_pw", ""), _aes_key_bytes()) if cfg.get("ldap_bind_pw") else ""
    client = LdapClient(
        LdapConfig(
            server=cfg.get("ldap_server", ""),
            bind_dn=cfg.get("ldap_bind_dn", ""),
            bind_pw=bind_pw,
            base_dn=cfg.get("ldap_base_dn", ""),
            user_filter=cfg.get("ldap_user_filter", "((&(objectClass=user)(sAMAccountName=%u)))"),
            group_dn=cfg.get("ldap_group_dn", ""),
        )
    )
    res = await client.test_connection()
    members = await client.list_group_members() if res.get("success") else []
    return {
        **res,
        "group_member_count": len(members),
        "sample_members": members[:5],
    }


def _tail_last_lines(path: Path, max_lines: int) -> list[str]:
    if not path.exists():
        return []
    data = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return data[-max_lines:]


@router.get("/log-stream")
async def log_stream():
    log_path = Path(settings.FR_LOG)

    async def event_gen():
        # initial tail
        for line in _tail_last_lines(log_path, 200):
            yield f"data: {line}\n\n"

        # follow
        try:
            with log_path.open("r", encoding="utf-8", errors="replace") as f:
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if line:
                        yield f"data: {line.rstrip()}\n\n"
                    else:
                        await asyncio.sleep(0.5)
        except Exception as e:
            yield f"data: [log-stream error] {str(e)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")

