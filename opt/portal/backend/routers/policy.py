from __future__ import annotations

from fastapi import APIRouter, Request

from ..config import settings
from ..models.policy import NasCreate, NasUpdate, PolicyUpdate
from ..services.audit import write_audit
from ..services.config_writer import writer
from ..services.crypto import encrypt_aes_gcm
from ..services.radius_db import delete_nas, get_app_config, get_nas_list, insert_nas, set_app_config, update_nas
from ._errors import api_error

router = APIRouter()


def _aes_key_bytes() -> bytes:
    return bytes.fromhex(settings.AES_KEY)


@router.get("/policy")
async def get_policy():
    cfg = await get_app_config(
        [
            "setup_complete",
            "auth_mode",
            "ldap_server",
            "ldap_bind_dn",
            "ldap_base_dn",
            "ldap_group_dn",
            "ldap_user_filter",
            "default_simultaneous_use",
            "radius_shared_secret",
            "ldap_bind_pw",
            "eap_cert_path",
        ]
    )
    nas = await get_nas_list()

    # never return secrets
    if cfg.get("radius_shared_secret"):
        cfg["radius_shared_secret"] = "****"
    if cfg.get("ldap_bind_pw"):
        cfg["ldap_bind_pw"] = "****"

    return {"config": cfg, "nas": nas}


@router.put("/policy")
async def update_policy(payload: PolicyUpdate, request: Request):
    existing = await get_app_config()
    updates: dict[str, str] = {}

    if payload.auth_mode is not None:
        updates["auth_mode"] = payload.auth_mode
    if payload.ldap_server is not None:
        updates["ldap_server"] = payload.ldap_server
    if payload.ldap_bind_dn is not None:
        updates["ldap_bind_dn"] = payload.ldap_bind_dn
    if payload.ldap_base_dn is not None:
        updates["ldap_base_dn"] = payload.ldap_base_dn
    if payload.ldap_group_dn is not None:
        updates["ldap_group_dn"] = payload.ldap_group_dn
    if payload.ldap_user_filter is not None:
        updates["ldap_user_filter"] = payload.ldap_user_filter
    if payload.default_simultaneous_use is not None:
        updates["default_simultaneous_use"] = str(payload.default_simultaneous_use)

    if payload.ldap_bind_pw is not None:
        updates["ldap_bind_pw"] = encrypt_aes_gcm(payload.ldap_bind_pw, _aes_key_bytes())

    if payload.radius_shared_secret is not None:
        updates["radius_shared_secret"] = encrypt_aes_gcm(payload.radius_shared_secret, _aes_key_bytes())

    if not updates:
        raise api_error(422, "policy.validation", "No changes provided.")

    await set_app_config(updates)
    r = await writer.write_all(admin_user=request.state.user.get("sub"), ip_address=request.client.host if request.client else None)
    if not r.get("success"):
        raise api_error(500, "config.reload_failed", f"FreeRADIUS reload failed: {r.get('stderr','')}")

    await write_audit(
        admin_user=request.state.user.get("sub"),
        action="policy.update",
        target="global",
        detail={"keys": list(updates.keys())},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.get("/nas")
async def nas_list():
    return await get_nas_list()


@router.post("/nas")
async def nas_create(payload: NasCreate, request: Request):
    await insert_nas(payload.nasname, payload.shortname, payload.secret, payload.description)
    r = await writer.write_all(admin_user=request.state.user.get("sub"), ip_address=request.client.host if request.client else None)
    if not r.get("success"):
        raise api_error(500, "config.reload_failed", f"FreeRADIUS reload failed: {r.get('stderr','')}")
    await write_audit(
        admin_user=request.state.user.get("sub"),
        action="nas.create",
        target=payload.shortname,
        detail={"nasname": payload.nasname},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.put("/nas/{nas_id}")
async def nas_update(nas_id: int, payload: NasUpdate, request: Request):
    await update_nas(nas_id, payload.nasname, payload.shortname, payload.secret, payload.description)
    r = await writer.write_all(admin_user=request.state.user.get("sub"), ip_address=request.client.host if request.client else None)
    if not r.get("success"):
        raise api_error(500, "config.reload_failed", f"FreeRADIUS reload failed: {r.get('stderr','')}")
    await write_audit(
        admin_user=request.state.user.get("sub"),
        action="nas.update",
        target=str(nas_id),
        detail={"shortname": payload.shortname},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.delete("/nas/{nas_id}")
async def nas_delete(nas_id: int, request: Request):
    await delete_nas(nas_id)
    r = await writer.write_all(admin_user=request.state.user.get("sub"), ip_address=request.client.host if request.client else None)
    if not r.get("success"):
        raise api_error(500, "config.reload_failed", f"FreeRADIUS reload failed: {r.get('stderr','')}")
    await write_audit(
        admin_user=request.state.user.get("sub"),
        action="nas.delete",
        target=str(nas_id),
        detail={},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}

