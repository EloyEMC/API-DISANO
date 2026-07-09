"""
Sistema de Rate Limiting usando slowapi
=======================================

Este módulo implementa limitación de tasa de peticiones para prevenir:
- Scraping masivo de datos
- Ataques DoS
- Agotamiento de recursos

Usa slowapi (wrapper de slowapi para FastAPI) con almacenamiento en memoria.
Para producción con múltiples workers, se recomienda usar Redis.

Configuración:
    RATE_LIMIT_PER_CLIENT: 30 peticiones/minuto por API key
    RATE_LIMIT_GLOBAL: 1000 peticiones/minuto totales
    RATE_LIMIT_BURST: 10 peticiones máximas en burst

Uso:
    from app.security.rate_limiter import limiter
    from fastapi import FastAPI

    app = FastAPI()
    app.state.limiter = limiter

    @app.get("/productos")
    @limiter.limit("30/minute")
    async def get_productos():
        pass
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import get_settings
from app.security.logging_config import logger, log_security_event

settings = get_settings()


def get_api_key_identifier(request: Request) -> str:
    """
    Genera un identificador único para rate limiting basado en API key.

    Si hay API key, usa la key como identificador (rate limiting por cliente).
    Si no hay API key, usa IP address como fallback.

    Esto permite que cada cliente con su propia API key tenga su propio límite,
    en lugar de compartir el límite global.

    Args:
        request: Objeto Request de FastAPI

    Returns:
        str: Identificador único (api_key:xxxxx o ip:xxxxx)

    Ejemplo:
        # Con API key:
        "api_key:abc12345"

        # Sin API key:
        "ip:192.168.1.1"
    """
    # Intentar obtener API key del header
    api_key = request.headers.get(settings.api_key_header)

    if api_key:
        # Usar API key como identificador
        # Solo mostrar primeros 8 caracteres por seguridad
        key_preview = f"{api_key[:8]}" if len(api_key) > 8 else api_key
        identifier = f"api_key:{key_preview}"
        logger.debug(f"Rate limiting por API key: {identifier}")
    else:
        # Fallback a IP address
        identifier = f"ip:{get_remote_address(request)}"
        logger.debug(f"Rate limiting por IP: {identifier}")

    return identifier


# Crear instancia del limiter
# Usa el identificador personalizado basado en API key
limiter = Limiter(
    key_func=get_api_key_identifier,
    default_limits=[
        f"{settings.rate_limit_per_client}/minute",  # 30 peticiones/minuto
        f"{settings.rate_limit_burst}/10seconds"     # 10 peticiones/10segundos
    ],
    storage_uri="memory://",  # En producción usar: "redis://localhost:6379"
    enabled=settings.rate_limit_enabled
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler para rate limit exceeded.

    Cuando un cliente excede el rate limit, esta función retorna una respuesta
    JSON amigable en lugar del HTML default de slowapi.

    Args:
        request: Objeto Request de FastAPI
        exc: Excepción RateLimitExceeded

    Returns:
        dict: Respuesta JSON con detalle del error

    Ejemplo de respuesta:
        {
            "detail": {
                "error": "Rate limit exceeded",
                "message": "Has excedido el límite de peticiones.",
                "retry_after": 45
            }
        }
    """
    identifier = get_api_key_identifier(request)
    logger.warning(
        f"Rate limit excedido por {identifier}. "
        f"Límite: {settings.rate_limit_per_client}/minute"
    )
    log_security_event(
        event_type="rate_limit",
        details=f"Exceeded {settings.rate_limit_per_client}/minute",
        api_key=identifier.split(":")[-1] if "api_key:" in identifier else "none"
    )

    return {
        "detail": {
            "error": "Rate limit exceeded",
            "message": (
                f"Has excedido el límite de peticiones. "
                f"Máximo {settings.rate_limit_per_client} peticiones cada 60 segundos."
            ),
            "retry_after": getattr(exc, 'retry_after', 60)
        }
    }
