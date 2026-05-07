from __future__ import annotations

from pydantic import BaseModel, Field


class LocalUserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)
    simultaneous_use: int | None = Field(default=None, ge=1, le=10)


class LocalUserUpdate(BaseModel):
    password: str | None = Field(default=None, min_length=1, max_length=128)
    simultaneous_use: int | None = Field(default=None, ge=1, le=10)


class BlockReason(BaseModel):
    reason: str | None = None

