from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from ..database import db_conn

router = APIRouter()


def _build_filters(
    username: str | None,
    nas_ip: str | None,
    ssid: str | None,
    from_date: str | None,
    to_date: str | None,
):
    where: list[str] = []
    params: list[Any] = []
    if username:
        where.append("username = %s")
        params.append(username)
    if nas_ip:
        where.append("nasipaddress = %s")
        params.append(nas_ip)
    if ssid:
        where.append("calledstationid LIKE %s")
        params.append(f"%{ssid}%")
    if from_date:
        where.append("acctstarttime >= %s")
        params.append(from_date)
    if to_date:
        where.append("acctstarttime <= %s")
        params.append(to_date)
    return where, params


@router.get("")
async def list_accounting(
    username: str | None = None,
    nas_ip: str | None = None,
    ssid: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
):
    where, params = _build_filters(username, nas_ip, ssid, from_date, to_date)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    offset = (page - 1) * per_page

    async with db_conn() as (_conn, cur):
        await cur.execute(f"SELECT COUNT(*) AS c FROM radacct {where_sql}", tuple(params))
        total = (await cur.fetchone())["c"]

        await cur.execute(
            f"""
            SELECT
              radacctid, acctsessionid, acctuniqueid, username, realm, nasipaddress,
              acctstarttime, acctstoptime, acctsessiontime,
              acctinputoctets, acctoutputoctets,
              calledstationid, callingstationid, acctterminatecause, framedipaddress
            FROM radacct
            {where_sql}
            ORDER BY acctstarttime DESC
            LIMIT %s OFFSET %s
            """,
            tuple(params) + (per_page, offset),
        )
        rows = await cur.fetchall()

    return {"page": page, "per_page": per_page, "total": int(total), "items": rows}


@router.get("/export")
async def export_csv(
    username: str | None = None,
    nas_ip: str | None = None,
    ssid: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
):
    where, params = _build_filters(username, nas_ip, ssid, from_date, to_date)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    async def gen():
        header = [
            "radacctid",
            "acctsessionid",
            "acctuniqueid",
            "username",
            "nasipaddress",
            "acctstarttime",
            "acctstoptime",
            "acctsessiontime",
            "acctinputoctets",
            "acctoutputoctets",
            "calledstationid",
            "callingstationid",
            "acctterminatecause",
            "framedipaddress",
        ]
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(header)
        yield buf.getvalue().encode("utf-8")

        async with db_conn() as (_conn, cur):
            await cur.execute(
                f"""
                SELECT
                  radacctid, acctsessionid, acctuniqueid, username, nasipaddress,
                  acctstarttime, acctstoptime, acctsessiontime,
                  acctinputoctets, acctoutputoctets,
                  calledstationid, callingstationid, acctterminatecause, framedipaddress
                FROM radacct
                {where_sql}
                ORDER BY acctstarttime DESC
                """,
                tuple(params),
            )
            rows = await cur.fetchall()

        for r in rows:
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow([r.get(k) for k in header])
            yield buf.getvalue().encode("utf-8")

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        gen(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="accounting_{ts}.csv"'},
    )

