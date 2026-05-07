from __future__ import annotations

import bcrypt
from fastapi import APIRouter, Request

from ..config import settings
from ..database import db_conn
from ..models.setup import SetupPayload, TestLdapPayload
from ..services.audit import write_audit
from ..services.config_writer import writer
from ..services.crypto import encrypt_aes_gcm
from ..services.ldap_client import LdapClient, LdapConfig
from ..services.radius_db import insert_nas, is_setup_complete, set_app_config
from ._errors import api_error

router = APIRouter()


def _aes_key_bytes() -> bytes:
    return bytes.fromhex(settings.AES_KEY)


@router.get("/status")
async def status():
    return {"setup_complete": await is_setup_complete()}


@router.post("/test-ldap")
async def test_ldap(payload: TestLdapPayload):
    cfg = LdapConfig(
        server=payload.ldap_server,
        bind_dn=payload.ldap_bind_dn,
        bind_pw=payload.ldap_bind_pw,
        base_dn=payload.ldap_base_dn,
        user_filter=payload.ldap_user_filter,
        group_dn=payload.ldap_group_dn,
    )
    client = LdapClient(cfg)
    return await client.test_connection()


@router.post("/init")
async def init_setup(payload: SetupPayload, request: Request):
    if await is_setup_complete():
        raise api_error(409, "setup.already_complete", "Setup has already been completed.")

    includes_ldap = payload.auth_mode in ("ldap", "hybrid")
    if includes_ldap:
        missing = [
            k
            for k in [
                ("ldap_server", payload.ldap_server),
                ("ldap_bind_dn", payload.ldap_bind_dn),
                ("ldap_bind_pw", payload.ldap_bind_pw),
                ("ldap_base_dn", payload.ldap_base_dn),
                ("ldap_group_dn", payload.ldap_group_dn),
            ]
            if not k[1]
        ]
        if missing:
            raise api_error(422, "setup.validation", f"Missing LDAP fields: {', '.join([m[0] for m in missing])}")

        cfg = LdapConfig(
            server=payload.ldap_server or "",
            bind_dn=payload.ldap_bind_dn or "",
            bind_pw=payload.ldap_bind_pw or "",
            base_dn=payload.ldap_base_dn or "",
            user_filter=payload.ldap_user_filter or "((&(objectClass=user)(sAMAccountName=%u)))",
            group_dn=payload.ldap_group_dn or "",
        )
        client = LdapClient(cfg)
        res = await client.test_connection()
        if not res.get("success"):
            raise api_error(400, "ldap.test_failed", "LDAP test connection failed.")

    enc_bind_pw = encrypt_aes_gcm(payload.ldap_bind_pw or "", _aes_key_bytes()) if includes_ldap else ""
    enc_secret = encrypt_aes_gcm(payload.radius_shared_secret, _aes_key_bytes())

    await set_app_config(
        {
            "setup_complete": "0",
            "auth_mode": payload.auth_mode,
            "ldap_server": payload.ldap_server or "",
            "ldap_bind_dn": payload.ldap_bind_dn or "",
            "ldap_bind_pw": enc_bind_pw if includes_ldap else "",
            "ldap_base_dn": payload.ldap_base_dn or "",
            "ldap_group_dn": payload.ldap_group_dn or "",
            "ldap_user_filter": payload.ldap_user_filter or "((&(objectClass=user)(sAMAccountName=%u)))",
            "default_simultaneous_use": "2",
            "radius_shared_secret": enc_secret,
            "eap_cert_path": payload.eap_cert_path or "",
        }
    )

    # Create NAS entry for AC
    await insert_nas(
        nasname=payload.ac_ip,
        shortname=payload.ac_shortname,
        secret=payload.radius_shared_secret,
        description=payload.ac_description,
    )

    # Create portal admin account
    pw_hash = bcrypt.hashpw(payload.admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    async with db_conn() as (_conn, cur):
        await cur.execute(
            """
            INSERT INTO portal_users (username, password_hash, role)
            VALUES (%s, %s, 'admin')
            """,
            (payload.admin_username, pw_hash),
        )

    # Write FreeRADIUS configs & reload
    r = await writer.write_all(admin_user=payload.admin_username, ip_address=request.client.host if request.client else None)
    if not r.get("success"):
        raise api_error(500, "config.reload_failed", f"FreeRADIUS reload failed: {r.get('stderr','')}")

    await set_app_config({"setup_complete": "1"})
    await write_audit(
        admin_user=payload.admin_username,
        action="setup.complete",
        target="portal",
        detail={"auth_mode": payload.auth_mode, "ac_ip": payload.ac_ip},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}

