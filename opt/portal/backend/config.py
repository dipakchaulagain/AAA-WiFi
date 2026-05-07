from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="/opt/portal/.env", env_file_encoding="utf-8")

    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_NAME: str = "radius"
    DB_USER: str = "portaluser"
    DB_PASS: str

    JWT_SECRET: str
    AES_KEY: str  # 32-byte hex

    FR_CONFIG_DIR: str = "/etc/freeradius/3.0"
    FR_LOG: str = "/var/log/freeradius/radius.log"

    PORTAL_VLAN_IP: str | None = None


settings = Settings()

