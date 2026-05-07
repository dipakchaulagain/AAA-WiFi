from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from ldap3 import ALL, SUBTREE, Connection, Server, Tls


@dataclass
class LdapConfig:
    server: str
    bind_dn: str
    bind_pw: str
    base_dn: str
    user_filter: str
    group_dn: str


class LdapClient:
    def __init__(self, cfg: LdapConfig):
        self.cfg = cfg
        self._sem = asyncio.Semaphore(5)

    def _server(self) -> Server:
        tls = Tls(validate=2)  # CERT_REQUIRED, use system trust
        # ldap3 uses server string like "ldaps://host" or host; we keep user-provided url
        return Server(self.cfg.server, use_ssl=True, tls=tls, get_info=ALL, connect_timeout=30)

    async def _with_conn(self, fn):
        async with self._sem:
            return await asyncio.to_thread(fn)

    async def test_connection(self) -> dict[str, Any]:
        def _run():
            s = self._server()
            c = Connection(s, user=self.cfg.bind_dn, password=self.cfg.bind_pw, auto_bind=True, receive_timeout=30)
            info = {
                "success": True,
                "server": str(s),
                "vendor": getattr(s.info, "vendor_name", None),
                "version": getattr(s.info, "vendor_version", None),
            }
            c.unbind()
            return info

        try:
            return await self._with_conn(_run)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_group_members(self) -> list[dict[str, Any]]:
        def _run():
            s = self._server()
            c = Connection(s, user=self.cfg.bind_dn, password=self.cfg.bind_pw, auto_bind=True, receive_timeout=30)
            # AD: group "member" attribute contains DNs
            c.search(self.cfg.group_dn, "(objectClass=group)", attributes=["member"])
            if not c.entries:
                c.unbind()
                return []
            members = c.entries[0].member.values if "member" in c.entries[0] else []
            out: list[dict[str, Any]] = []
            for dn in members:
                c.search(
                    search_base=dn,
                    search_filter="(objectClass=person)",
                    search_scope=SUBTREE,
                    attributes=["sAMAccountName", "displayName", "mail", "distinguishedName"],
                )
                if not c.entries:
                    continue
                e = c.entries[0]
                out.append(
                    {
                        "sAMAccountName": str(getattr(e, "sAMAccountName", "") or ""),
                        "displayName": str(getattr(e, "displayName", "") or ""),
                        "mail": str(getattr(e, "mail", "") or ""),
                        "distinguishedName": str(getattr(e, "distinguishedName", "") or ""),
                    }
                )
            c.unbind()
            return out

        return await self._with_conn(_run)

    async def user_in_group(self, username: str) -> bool:
        # Strategy: search user DN by filter, then check group membership filter.
        def _run():
            s = self._server()
            c = Connection(s, user=self.cfg.bind_dn, password=self.cfg.bind_pw, auto_bind=True, receive_timeout=30)
            filt = self.cfg.user_filter.replace("%u", username)
            c.search(self.cfg.base_dn, filt, search_scope=SUBTREE, attributes=["distinguishedName", "memberOf"])
            if not c.entries:
                c.unbind()
                return False
            e = c.entries[0]
            member_of = set((e.memberOf.values if "memberOf" in e else []))
            c.unbind()
            return self.cfg.group_dn in member_of

        return await self._with_conn(_run)

