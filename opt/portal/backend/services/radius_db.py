from __future__ import annotations

from typing import Any

from ..database import db_conn


async def get_app_config(keys: list[str] | None = None) -> dict[str, str]:
    async with db_conn() as (_conn, cur):
        if keys:
            placeholders = ",".join(["%s"] * len(keys))
            await cur.execute(f"SELECT `key`, value FROM app_config WHERE `key` IN ({placeholders})", tuple(keys))
        else:
            await cur.execute("SELECT `key`, value FROM app_config")
        rows = await cur.fetchall()
    return {r["key"]: (r["value"] or "") for r in rows}


async def set_app_config(values: dict[str, str]) -> None:
    async with db_conn() as (_conn, cur):
        for k, v in values.items():
            await cur.execute(
                """
                INSERT INTO app_config (`key`, value) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE value = VALUES(value)
                """,
                (k, v),
            )


async def is_setup_complete() -> bool:
    cfg = await get_app_config(["setup_complete"])
    return cfg.get("setup_complete", "0") == "1"


async def get_nas_list() -> list[dict[str, Any]]:
    async with db_conn() as (_conn, cur):
        await cur.execute("SELECT id, nasname, shortname, type, secret, server, community, description FROM nas ORDER BY id ASC")
        return await cur.fetchall()


async def insert_nas(nasname: str, shortname: str, secret: str, description: str | None) -> None:
    async with db_conn() as (_conn, cur):
        await cur.execute(
            """
            INSERT INTO nas (nasname, shortname, type, secret, description)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (nasname, shortname, "other", secret, description),
        )


async def update_nas(nas_id: int, nasname: str, shortname: str, secret: str | None, description: str | None) -> None:
    async with db_conn() as (_conn, cur):
        if secret is None:
            await cur.execute(
                "UPDATE nas SET nasname=%s, shortname=%s, description=%s WHERE id=%s",
                (nasname, shortname, description, nas_id),
            )
        else:
            await cur.execute(
                "UPDATE nas SET nasname=%s, shortname=%s, secret=%s, description=%s WHERE id=%s",
                (nasname, shortname, secret, description, nas_id),
            )


async def delete_nas(nas_id: int) -> None:
    async with db_conn() as (_conn, cur):
        await cur.execute("DELETE FROM nas WHERE id=%s", (nas_id,))


async def radcheck_get(username: str) -> list[dict[str, Any]]:
    async with db_conn() as (_conn, cur):
        await cur.execute("SELECT id, username, attribute, op, value FROM radcheck WHERE username=%s ORDER BY id ASC", (username,))
        return await cur.fetchall()


async def radcheck_upsert(username: str, attribute: str, op: str, value: str) -> None:
    async with db_conn() as (_conn, cur):
        await cur.execute(
            "SELECT id FROM radcheck WHERE username=%s AND attribute=%s LIMIT 1",
            (username, attribute),
        )
        row = await cur.fetchone()
        if row:
            await cur.execute(
                "UPDATE radcheck SET op=%s, value=%s WHERE id=%s",
                (op, value, row["id"]),
            )
        else:
            await cur.execute(
                "INSERT INTO radcheck (username, attribute, op, value) VALUES (%s, %s, %s, %s)",
                (username, attribute, op, value),
            )


async def radcheck_insert(username: str, attribute: str, op: str, value: str) -> None:
    async with db_conn() as (_conn, cur):
        await cur.execute(
            "INSERT INTO radcheck (username, attribute, op, value) VALUES (%s, %s, %s, %s)",
            (username, attribute, op, value),
        )


async def radcheck_delete(username: str, attribute: str | None = None) -> None:
    async with db_conn() as (_conn, cur):
        if attribute is None:
            await cur.execute("DELETE FROM radcheck WHERE username=%s", (username,))
        else:
            await cur.execute("DELETE FROM radcheck WHERE username=%s AND attribute=%s", (username, attribute))


async def delete_user_all(username: str) -> None:
    async with db_conn() as (_conn, cur):
        await cur.execute("DELETE FROM radcheck WHERE username=%s", (username,))
        await cur.execute("DELETE FROM radreply WHERE username=%s", (username,))


async def list_local_users() -> list[dict[str, Any]]:
    async with db_conn() as (_conn, cur):
        await cur.execute(
            """
            SELECT DISTINCT username
            FROM radcheck
            WHERE attribute != 'Auth-Type'
            ORDER BY username ASC
            """
        )
        usernames = [r["username"] for r in await cur.fetchall()]

        out: list[dict[str, Any]] = []
        for u in usernames:
            await cur.execute(
                "SELECT value FROM radcheck WHERE username=%s AND attribute='Simultaneous-Use' LIMIT 1",
                (u,),
            )
            sim = await cur.fetchone()
            await cur.execute(
                "SELECT 1 AS blocked FROM radcheck WHERE username=%s AND attribute='Auth-Type' AND op=':=' AND value='Reject' LIMIT 1",
                (u,),
            )
            blocked = await cur.fetchone()
            await cur.execute(
                "SELECT authdate FROM radpostauth WHERE username=%s ORDER BY authdate DESC LIMIT 1",
                (u,),
            )
            last = await cur.fetchone()
            out.append(
                {
                    "username": u,
                    "simultaneous_use": int(sim["value"]) if sim and str(sim["value"]).isdigit() else None,
                    "blocked": bool(blocked),
                    "last_seen": last["authdate"].isoformat() if last and last.get("authdate") else None,
                }
            )
        return out


async def get_active_sessions(limit: int | None = None) -> list[dict[str, Any]]:
    async with db_conn() as (_conn, cur):
        sql = """
        SELECT
          radacctid, acctsessionid, acctuniqueid, username, nasipaddress, acctstarttime,
          callingstationid, calledstationid, framedipaddress,
          UNIX_TIMESTAMP() - UNIX_TIMESTAMP(acctstarttime) AS duration_seconds
        FROM radacct
        WHERE acctstoptime IS NULL
        ORDER BY acctstarttime DESC
        """
        if limit:
            sql += " LIMIT %s"
            await cur.execute(sql, (limit,))
        else:
            await cur.execute(sql)
        return await cur.fetchall()


async def get_session_by_id(radacctid: int) -> dict[str, Any] | None:
    async with db_conn() as (_conn, cur):
        await cur.execute("SELECT * FROM radacct WHERE radacctid=%s LIMIT 1", (radacctid,))
        return await cur.fetchone()


async def dashboard_summary() -> dict[str, Any]:
    async with db_conn() as (_conn, cur):
        await cur.execute("SELECT COUNT(*) AS c FROM radacct WHERE acctstoptime IS NULL")
        active = (await cur.fetchone())["c"]
        await cur.execute(
            "SELECT COUNT(*) AS c FROM radpostauth WHERE authdate >= (NOW() - INTERVAL 1 HOUR)"
        )
        attempts = (await cur.fetchone())["c"]
        await cur.execute(
            "SELECT COUNT(*) AS c FROM radpostauth WHERE reply LIKE 'Access-Reject%' AND authdate >= (NOW() - INTERVAL 1 HOUR)"
        )
        rejects = (await cur.fetchone())["c"]
        await cur.execute(
            """
            SELECT COUNT(DISTINCT username) AS c
            FROM radcheck
            WHERE attribute='Auth-Type' AND op=':=' AND value='Reject'
            """
        )
        blocked = (await cur.fetchone())["c"]
        return {
            "active_sessions": int(active),
            "auth_attempts_last_hour": int(attempts),
            "failed_auths_last_hour": int(rejects),
            "blocked_users": int(blocked),
        }

