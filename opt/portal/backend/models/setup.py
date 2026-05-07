from __future__ import annotations

from pydantic import BaseModel, Field


class SetupPayload(BaseModel):
    auth_mode: str = Field(pattern="^(db|ldap|hybrid)$")

    ldap_server: str | None = None
    ldap_bind_dn: str | None = None
    ldap_bind_pw: str | None = None
    ldap_base_dn: str | None = None
    ldap_group_dn: str | None = None
    ldap_user_filter: str | None = None

    radius_shared_secret: str = Field(min_length=6)
    ac_ip: str = Field(min_length=7)
    ac_shortname: str = Field(default="huawei-ac", min_length=2)
    ac_description: str | None = None

    eap_cert_path: str | None = None

    admin_username: str = Field(min_length=3, max_length=64)
    admin_password: str = Field(min_length=8, max_length=128)


class TestLdapPayload(BaseModel):
    ldap_server: str
    ldap_bind_dn: str
    ldap_bind_pw: str
    ldap_base_dn: str
    ldap_group_dn: str
    ldap_user_filter: str = "((&(objectClass=user)(sAMAccountName=%u)))"

