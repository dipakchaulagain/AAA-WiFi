from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import settings
from .audit import write_audit
from .crypto import decrypt_aes_gcm
from .radius_db import get_app_config, get_nas_list


def _aes_key_bytes() -> bytes:
    return bytes.fromhex(settings.AES_KEY)


class ConfigWriter:
    def __init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(Path(__file__).resolve().parents[1] / "templates"),
            autoescape=select_autoescape(enabled_extensions=()),
            keep_trailing_newline=True,
        )

    async def write_all(self, admin_user: str | None, ip_address: str | None) -> dict[str, Any]:
        cfg = await get_app_config()
        nas_list = await get_nas_list()

        def _maybe_decrypt(key: str) -> str | None:
            v = cfg.get(key)
            if not v:
                return None
            return decrypt_aes_gcm(v, _aes_key_bytes())

        ldap_bind_pw = _maybe_decrypt("ldap_bind_pw") or ""
        radius_shared_secret = _maybe_decrypt("radius_shared_secret") or ""

        render_ctx = {
            "ldap_server": cfg.get("ldap_server", ""),
            "ldap_bind_dn": cfg.get("ldap_bind_dn", ""),
            "ldap_bind_pw": ldap_bind_pw,
            "ldap_base_dn": cfg.get("ldap_base_dn", ""),
            "ldap_group_dn": cfg.get("ldap_group_dn", ""),
            "ldap_user_filter": cfg.get("ldap_user_filter", "((&(objectClass=user)(sAMAccountName=%u)))"),
            "default_simultaneous_use": cfg.get("default_simultaneous_use", "2"),
            "radius_shared_secret": radius_shared_secret,
            "db_pass": settings.DB_PASS,
            "nas_list": nas_list,
        }

        fr_dir = Path(settings.FR_CONFIG_DIR)
        targets: list[tuple[str, Path]] = [
            ("ldap.conf.j2", fr_dir / "mods-enabled" / "ldap"),
            ("sql.conf.j2", fr_dir / "mods-enabled" / "sql"),
            ("clients.conf.j2", fr_dir / "clients.conf"),
            ("concurrent_limit.j2", fr_dir / "policy.d" / "concurrent_limit"),
        ]

        backups: list[tuple[Path, Path]] = []
        written: list[Path] = []

        def _backup(p: Path) -> Path:
            bak = p.with_suffix(p.suffix + ".bak") if p.suffix else Path(str(p) + ".bak")
            if p.exists():
                shutil.copy2(p, bak)
                backups.append((p, bak))
            return bak

        try:
            for _tmpl, dest in targets:
                dest.parent.mkdir(parents=True, exist_ok=True)
                _backup(dest)

            for tmpl_name, dest in targets:
                txt = self.env.get_template(tmpl_name).render(**render_ctx)
                dest.write_text(txt, encoding="utf-8")
                written.append(dest)

            proc = subprocess.run(
                ["sudo", "/bin/systemctl", "reload", "freeradius"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )
            ok = proc.returncode == 0
            stderr = (proc.stderr or b"").decode("utf-8", errors="replace")

            if not ok:
                # restore backups
                for orig, bak in backups:
                    if bak.exists():
                        shutil.copy2(bak, orig)
                await write_audit(
                    admin_user=admin_user,
                    action="config.reload_failed",
                    target="freeradius",
                    detail={"stderr": stderr},
                    ip_address=ip_address,
                )
                return {"success": False, "stderr": stderr}

            await write_audit(
                admin_user=admin_user,
                action="config.reload",
                target="freeradius",
                detail={"files": [str(p) for p in written]},
                ip_address=ip_address,
            )
            return {"success": True}
        except Exception as e:
            # best-effort restore
            for orig, bak in backups:
                try:
                    if bak.exists():
                        shutil.copy2(bak, orig)
                except Exception:
                    pass
            await write_audit(
                admin_user=admin_user,
                action="config.write_exception",
                target="freeradius",
                detail={"error": str(e)},
                ip_address=ip_address,
            )
            return {"success": False, "stderr": str(e)}


writer = ConfigWriter()

