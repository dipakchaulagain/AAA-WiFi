from __future__ import annotations

from pydantic import BaseModel, Field


class PolicyUpdate(BaseModel):
    auth_mode: str | None = Field(default=None, pattern="^(db|ldap|hybrid)$")
    ldap_server: str | None = None
    ldap_bind_dn: str | None = None
    ldap_bind_pw: str | None = None
    ldap_base_dn: str | None = None
    ldap_group_dn: str | None = None
    ldap_user_filter: str | None = None
    default_simultaneous_use: int | None = Field(default=None, ge=1, le=10)
    radius_shared_secret: str | None = None


class NasCreate(BaseModel):
    nasname: str
    shortname: str
    secret: str
    description: str | None = None


class NasUpdate(BaseModel):
    nasname: str
    shortname: str
    secret: str | None = None
    description: str | None = None

