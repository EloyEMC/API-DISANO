"""
Configuración centralizada de la aplicación
Usa pydantic-settings para validación y type safety
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
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
    environment: str = "development"  # development | production

    # Security - API Keys
    api_keys: List[str] = []
    api_key_header: str = "X-API-Key"

    # Security - Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_client: int = 30  # Peticiones por minuto por cliente
    rate_limit_global: int = 1000  # Peticiones por minuto totales
    rate_limit_burst: int = 10  # Máximo peticiones en burst
    rate_limit_listings: int = 10  # Peticiones/min para listados

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

    # Security - CORS
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # Security - HTTPS
    https_enabled: bool = True
    https_hsts_max_age: int = 31536000  # 1 año
    https_hsts_include_subdomains: bool = True
    https_hsts_preload: bool = True

    # Security - Documentation
    docs_enabled: bool = False  # Totalmente deshabilitada

    # Security - Scraping Detection
    scraping_detection_enabled: bool = True
    ban_enabled: bool = True
    ban_duration_first_offense: int = 3600  # 1 hora
    ban_duration_second_offense: int = 86400  # 24 horas

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/api.log"
    log_rotation: str = "500 MB"
    log_retention: str = "10 days"
    security_log_enabled: bool = True

    # Database
    database_path: str = "database/tarifa_disano.db"

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
