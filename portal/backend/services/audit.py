from __future__ import annotations

import json
from typing import Any

from ..database import db_conn


async def write_audit(
    admin_user: str | None,
    action: str,
    target: str | None,
    detail: dict[str, Any] | None,
    ip_address: str | None,
) -> None:
    async with db_conn() as (_conn, cur):
        await cur.execute(
            """
            INSERT INTO audit_log (admin_user, action, target, detail, ip_address)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (admin_user, action, target, json.dumps(detail or {}), ip_address),
        )

