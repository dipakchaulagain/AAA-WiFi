from __future__ import annotations

from fastapi import APIRouter

from ..services.radius_db import dashboard_summary, get_active_sessions

router = APIRouter()


@router.get("/summary")
async def summary():
    metrics = await dashboard_summary()
    recent = await get_active_sessions(limit=10)
    return {"metrics": metrics, "recent_sessions": recent}

