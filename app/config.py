"""Centralized application configuration.

Uses pydantic-settings for validation and type safety.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    api_title: str = "API Disano"
    api_description: str = "API REST para consultar productos y tarifas de Disano"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"
    secret_key: str = ""
    api_keys: str | list[str] = Field(default_factory=list)
    api_key_header: str = "X-API-Key"
    admin_api_keys: str | list[str] = Field(default_factory=list)
    bc3_api_keys: str | list[str] = Field(default_factory=list)
    # Approval is deliberately separate: normal processing keys never authorize writes.
    bc3_approval_keys: str | list[str] = Field(default_factory=list)
    bc3_preview_ttl_seconds: int = Field(default=900, ge=60, le=86400)
    bc3_approval_scope: str = "bc3-enrichment"
    bc3_approval_mode: Literal["github_review", "sole_maintainer"] = "github_review"
    github_api_token: str | None = None
    github_expected_repository: str | None = None
    github_api_url: str = "https://api.github.com"
    github_required_approvals: int = Field(default=1, ge=1, le=100)
    rate_limit_enabled: bool = True
    rate_limit_per_client: int = 60
    rate_limit_global: int = 1000
    rate_limit_burst: int = 10
    rate_limit_listings: int = 10
    blocked_user_agents: list[str] = [
        "python-requests",
        "curl",
        "wget",
        "scraper",
        "crawler",
        "bot",
        "spider",
        "headless",
        "phantom",
        "selenium",
    ]
    cors_origins: str | list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    https_enabled: bool = True
    https_hsts_max_age: int = 31536000
    https_hsts_include_subdomains: bool = True
    https_hsts_preload: bool = True
    docs_enabled: bool | None = None
    scraping_detection_enabled: bool = True
    ban_enabled: bool = True
    ban_duration_first_offense: int = 3600
    ban_duration_second_offense: int = 86400
    log_level: str = "INFO"
    log_file: str = "logs/api.log"
    log_rotation: str = "500 MB"
    log_retention: str = "10 days"
    security_log_enabled: bool = True
    database_url: str | None = None
    database_path: str = "database/tarifa_disano.db"

    @model_validator(mode="after")
    def set_docs_default(self) -> "Settings":
        """Set the documentation default according to the environment."""
        if self.docs_enabled is None:
            self.docs_enabled = not self.is_production()
        return self

    @field_validator(
        "api_keys", "admin_api_keys", "bc3_api_keys", "bc3_approval_keys", mode="before"
    )
    @classmethod
    def parse_key_lists(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated credentials into a list."""
        if isinstance(v, str):
            return [key.strip() for key in v.split(",") if key.strip()]
        return v if isinstance(v, list) else []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if isinstance(v, list) else ["*"]

    @property
    def api_keys_list(self) -> list[str]:
        """Return the general API credentials as a list."""
        return (
            self.api_keys
            if isinstance(self.api_keys, list)
            else ([self.api_keys] if self.api_keys else [])
        )

    @property
    def bc3_api_keys_list(self) -> list[str]:
        """Return the private BC3 API credentials as a list."""
        return (
            self.bc3_api_keys
            if isinstance(self.bc3_api_keys, list)
            else ([self.bc3_api_keys] if self.bc3_api_keys else [])
        )

    @property
    def bc3_approval_keys_list(self) -> list[str]:
        """Return the dedicated BC3 approval credentials as a list."""
        return (
            self.bc3_approval_keys
            if isinstance(self.bc3_approval_keys, list)
            else ([self.bc3_approval_keys] if self.bc3_approval_keys else [])
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Return configured CORS origins as a list."""
        return (
            self.cors_origins
            if isinstance(self.cors_origins, list)
            else ([self.cors_origins] if self.cors_origins else ["*"])
        )

    def is_production(self) -> bool:
        """Return whether the settings target production."""
        return self.environment.lower() == "production"

    def validate_required(self) -> None:
        """Validate settings required for production."""
        if not self.is_production():
            return
        missing = []
        if not self.secret_key or len(self.secret_key) < 32:
            missing.append("SECRET_KEY")
        if not self.api_keys_list:
            missing.append("API_KEYS")
        if missing:
            raise ValueError("Missing required production settings: " + ", ".join(missing))


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
