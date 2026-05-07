from __future__ import annotations

from pydantic import BaseModel


class DisconnectRequest(BaseModel):
    reason: str | None = None

