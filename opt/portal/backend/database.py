from __future__ import annotations

from contextlib import asynccontextmanager

import aiomysql

from .config import settings

_pool: aiomysql.Pool | None = None


async def init_db_pool() -> None:
    global _pool
    if _pool is not None:
        return
    _pool = await aiomysql.create_pool(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASS,
        db=settings.DB_NAME,
        autocommit=True,
        minsize=1,
        maxsize=10,
    )


async def close_db_pool() -> None:
    global _pool
    if _pool is None:
        return
    _pool.close()
    await _pool.wait_closed()
    _pool = None


@asynccontextmanager
async def db_conn():
    if _pool is None:
        await init_db_pool()
    assert _pool is not None
    async with _pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            yield conn, cur

