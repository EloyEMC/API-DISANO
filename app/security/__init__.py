"""
Módulo de seguridad para API_DISANO
===================================

Contiene todos los componentes de seguridad de la API:
- Autenticación mediante API Keys
- Rate limiting anti-scraping
- Filtro de User-Agent
- Detección de patrones de scraping
- Sistema de logging estructurado

Módulos:
    api_key: Validación de API Keys
    rate_limiter: Rate limiting con slowapi
    user_agent_filter: Filtro de User-Agents sospechosos
    scraping_detector: Detección heurística de scraping
    logging_config: Sistema de logs con loguru

Uso típico:
    from app.security import verify_api_key, limiter, logger, setup_logging

    # Setup logging al inicio
    setup_logging()

    # Proteger endpoint
    @router.get("/")
    @limiter.limit("30/minute")
    async def endpoint(api_key: str = Depends(verify_api_key)):
        logger.info("Endpoint accedido")
        pass
"""

from app.security.api_key import verify_api_key
from app.security.rate_limiter import limiter, get_api_key_identifier, rate_limit_exceeded_handler
from app.security.user_agent_filter import is_user_agent_allowed, get_user_agent_info
from app.security.scraping_detector import ScrapingDetector, detector
from app.security.logging_config import logger, setup_logging, log_access_request, log_security_event

__all__ = [
    # API Key
    "verify_api_key",

    # Rate Limiting
    "limiter",
    "get_api_key_identifier",
    "rate_limit_exceeded_handler",

    # User-Agent Filter
    "is_user_agent_allowed",
    "get_user_agent_info",

    # Scraping Detector
    "ScrapingDetector",
    "detector",

    # Logging
    "logger",
    "setup_logging",
    "log_access_request",
    "log_security_event"
]
