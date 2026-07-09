"""
Configuración centralizada de la aplicación
Usa pydantic-settings para validación y type safety
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from typing import List, Union
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Configuration
    api_title: str = "API Disano"
    api_description: str = "API REST para consultar productos y tarifas de Disano"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Environment
    environment: str = "development"

    # Security - API Keys (accept string or list, normalize to list)
    api_keys: Union[str, List[str]] = Field(default_factory=list)
    api_key_header: str = "X-API-Key"
    admin_api_keys: List[str] = []

    # Security - Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_client: int = 30
    rate_limit_global: int = 1000
    rate_limit_burst: int = 10
    rate_limit_listings: int = 10

    # Security - User-Agent Filtering
    blocked_user_agents: List[str] = [
        "python-requests",
        "curl",
        "wget",
        "scraper",
        "crawler",
        "bot",
        "spider",
        "headless",
        "phantom",
        "selenium"
    ]

    # Security - CORS (accept string or list, normalize to list)
    cors_origins: Union[str, List[str]] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # Security - HTTPS
    https_enabled: bool = True
    https_hsts_max_age: int = 31536000
    https_hsts_include_subdomains: bool = True
    https_hsts_preload: bool = True

    # Security - Documentation
    docs_enabled: bool = False

    # Security - Scraping Detection
    scraping_detection_enabled: bool = True
    ban_enabled: bool = True
    ban_duration_first_offense: int = 3600
    ban_duration_second_offense: int = 86400

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/api.log"
    log_rotation: str = "500 MB"
    log_retention: str = "10 days"
    security_log_enabled: bool = True

    # Database
    database_path: str = "database/tarifa_disano.db"

    @field_validator("api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse api_keys from string or list"""
        if isinstance(v, str):
            return [key.strip() for key in v.split(",") if key.strip()]
        return v if isinstance(v, list) else []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse cors_origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v if isinstance(v, list) else ["*"]

    @property
    def api_keys_list(self) -> List[str]:
        """Return api_keys as a list for compatibility"""
        if isinstance(self.api_keys, list):
            return self.api_keys
        return [self.api_keys] if self.api_keys else []

    @property
    def cors_origins_list(self) -> List[str]:
        """Return cors_origins as a list for compatibility"""
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        return [self.cors_origins] if self.cors_origins else ["*"]

    def is_production(self) -> bool:
        """Verifica si estamos en producción"""
        return self.environment.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instancia caché de Settings.
    Usa lru_cache para solo cargar una vez.
    """
    return Settings()
