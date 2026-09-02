from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+asyncpg://oligospace:change-me@postgres:5432/oligospace"
    auth_mode: Literal["oidc", "development"] = "development"
    oidc_issuer: AnyHttpUrl = AnyHttpUrl("http://keycloak:8080/realms/oligospace")
    oidc_audience: str = "oligospace-api"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    log_level: str = "INFO"
    development_user_id: uuid.UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")
    development_organization_id: uuid.UUID = uuid.UUID("10000000-0000-0000-0000-000000000001")
    development_email: str = "admin@oligospace.local"
    development_display_name: str = "Local administrator"
    development_auth_secret: str = "development-only-change-me"

    def validate_runtime(self) -> None:
        if self.environment == "production" and self.auth_mode != "oidc":
            raise ValueError("AUTH_MODE must be oidc in production")
        if self.environment == "production" and "change-me" in self.database_url:
            raise ValueError("Production database credentials are not configured")

    @property
    def oidc_jwks_url(self) -> str:
        return f"{str(self.oidc_issuer).rstrip('/')}/protocol/openid-connect/certs"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime()
    return settings
