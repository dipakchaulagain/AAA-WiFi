from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from ..config import settings
from ..database import db_conn
from ..models.users import BlockReason, LocalUserCreate, LocalUserUpdate
from ..services.audit import write_audit
from ..services.crypto import decrypt_aes_gcm
from ..services.ldap_client import LdapClient, LdapConfig
from ..services.radius_db import (
    delete_user_all,
    get_app_config,
    list_local_users,
    radcheck_delete,
    radcheck_insert,
    radcheck_upsert,
)
from ._errors import api_error

router = APIRouter()


def _aes_key_bytes() -> bytes:
    return bytes.fromhex(settings.AES_KEY)


@router.get("/local")
async def local_list():
    return await list_local_users()


@router.post("/local")
async def local_create(payload: LocalUserCreate, request: Request):
    cfg = await get_app_config(["default_simultaneous_use"])
    sim = payload.simultaneous_use or int(cfg.get("default_simultaneous_use", "2") or "2")

    await radcheck_insert(payload.username, "Cleartext-Password", ":=", payload.password)
    await radcheck_upsert(payload.username, "Simultaneous-Use", ":=", str(sim))

    await write_audit(
        admin_user=request.state.user.get("sub"),
        action="user.create",
        target=payload.username,
        detail={"simultaneous_use": sim, "type": "local"},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.put("/local/{username}")
async def local_update(username: str, payload: LocalUserUpdate, request: Request):
    if payload.password is None and payload.simultaneous_use is None:
        raise api_error(422, "users.validation", "No changes provided.")

    if payload.password is not None:
        await radcheck_upsert(username, "Cleartext-Password", ":=", payload.password)
    if payload.simultaneous_use is not None:
        await radcheck_upsert(username, "Simultaneous-Use", ":=", str(payload.simultaneous_use))

    await write_audit(
        admin_user=request.state.user.get("sub"),
        action="user.update",
        target=username,
        detail={"type": "local"},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.delete("/local/{username}")
async def local_delete(username: str, request: Request):
    await delete_user_all(username)
    await write_audit(
        admin_user=request.state.user.get("sub"),
        action="user.delete",
        target=username,
        detail={"type": "local"},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.post("/local/{username}/block")
async def local_block(username: str, payload: BlockReason, request: Request):
    await radcheck_insert(username, "Auth-Type", ":=", "Reject")
    await write_audit(
        admin_user=request.state.user.get("sub"),
        action="user.block",
        target=username,
        detail={"type": "local", "reason": payload.reason},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.post("/local/{username}/unblock")
async def local_unblock(username: str, request: Request):
    await radcheck_delete(username, attribute="Auth-Type")
    await write_audit(
        admin_user=request.state.user.get("sub"),
        action="user.unblock",
        target=username,
        detail={"type": "local"},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


async def _ldap_client_from_config() -> LdapClient:
    cfg = await get_app_config(
        [
            "ldap_server",
            "ldap_bind_dn",
            "ldap_bind_pw",
            "ldap_base_dn",
            "ldap_group_dn",
            "ldap_user_filter",
        ]
    )
    if not cfg.get("ldap_server"):
        raise api_error(400, "ldap.not_configured", "LDAP is not configured.")
    bind_pw = decrypt_aes_gcm(cfg.get("ldap_bind_pw", ""), _aes_key_bytes()) if cfg.get("ldap_bind_pw") else ""
    lc = LdapConfig(
        server=cfg.get("ldap_server", ""),
        bind_dn=cfg.get("ldap_bind_dn", ""),
        bind_pw=bind_pw,
        base_dn=cfg.get("ldap_base_dn", ""),
        user_filter=cfg.get("ldap_user_filter", "((&(objectClass=user)(sAMAccountName=%u)))"),
        group_dn=cfg.get("ldap_group_dn", ""),
    )
    return LdapClient(lc)


@router.get("/ldap")
async def ldap_list():
    client = await _ldap_client_from_config()
    members = await client.list_group_members()

    async with db_conn() as (_conn, cur):
        out: list[dict[str, Any]] = []
        for m in members:
            u = m.get("sAMAccountName") or ""
            await cur.execute("SELECT authdate FROM radpostauth WHERE username=%s ORDER BY authdate DESC LIMIT 1", (u,))
            last = await cur.fetchone()
            await cur.execute("SELECT COUNT(*) AS c FROM radacct WHERE username=%s AND acctstoptime IS NULL", (u,))
            sess = await cur.fetchone()
            await cur.execute(
                "SELECT 1 AS blocked FROM radcheck WHERE username=%s AND attribute='Auth-Type' AND op=':=' AND value='Reject' LIMIT 1",
                (u,),
            )
            blocked = await cur.fetchone()
            out.append(
                {
                    **m,
                    "last_seen": last["authdate"].isoformat() if last and last.get("authdate") else None,
                    "current_sessions": int(sess["c"]) if sess else 0,
                    "blocked": bool(blocked),
                }
            )
    return out


@router.post("/ldap/{username}/block")
async def ldap_block(username: str, payload: BlockReason, request: Request):
    await radcheck_insert(username, "Auth-Type", ":=", "Reject")
    await write_audit(
        admin_user=request.state.user.get("sub"),
        action="user.block",
        target=username,
        detail={"type": "ldap", "reason": payload.reason},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.post("/ldap/{username}/unblock")
async def ldap_unblock(username: str, request: Request):
    await radcheck_delete(username, attribute="Auth-Type")
    await write_audit(
        admin_user=request.state.user.get("sub"),
        action="user.unblock",
        target=username,
        detail={"type": "ldap"},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}

