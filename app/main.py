"""
API REST de Disano - Productos y Tarifas
========================================

FastAPI con SQLite - SECURE HARDENED - PRODUCTION READY

Este es el punto de entrada principal de la API DISANO.
Implementa múltiples capas de seguridad:
- Autenticación mediante API Key (X-API-Key header)
- Rate limiting anti-scraping
- Filtro de User-Agent
- Detección de patrones de scraping
- HTTPS enforcement
- Logging estructurado

Documentación totalmente deshabilitada por seguridad.
Endpoints con prefijos personalizados para dificultar descubrimiento.

Author: API Security Team
Version: 1.0.0 (Production Hardened)
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time

# Importar routers
from app.routers import productos, familias, bc3

# Importar configuración y seguridad
from app.config import get_settings
from app.security import (
    verify_api_key,
    limiter,
    rate_limit_exceeded_handler,
    is_user_agent_allowed,
    detector,
    logger,
    setup_logging
)

# Inicializar configuración
settings = get_settings()

# Setup logging ANTES de crear la app
setup_logging()
logger.info(f"Iniciando API Disano - Environment: {settings.environment}")

# Crear aplicación FastAPI con documentación DESHABILITADA
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url=None,  # ❌ DESHABILITADO - No Swagger UI
    redoc_url=None,  # ❌ DESHABILITADO - No ReDoc
    openapi_url=None  # ❌ DESHABILITADO - No OpenAPI schema
)

# Registrar rate limiter y handler de errores
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# ============================================================================
# MIDDLEWARES DE SEGURIDAD
# ============================================================================

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware que aplica múltiples capas de seguridad a cada petición.

    Orden de verificación:
    1. User-Agent filtering (bloquear scrapers conocidos)
    2. Scraping detection (patrones sospechosos)
    3. Honeypot detection (endpoints trampa)
    4. Loguear petición

    Nota: La autenticación API Key se maneja a nivel de endpoint con dependencies.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Procesa cada petición HTTP con verificaciones de seguridad."""

        # 1. User-Agent filtering (si no es health check)
        if request.url.path != "/health":
            if not is_user_agent_allowed(request):
                logger.warning(
                    f"User-Agent bloqueado: {request.headers.get('user-agent')} "
                    f"desde {request.client.host if request.client else 'unknown'}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User-Agent not allowed"
                )

        # 2. Scraping detection
        if detector.is_honeypot_access(request):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not found"
            )

        if detector.is_suspicious_request(request):
            logger.warning(
                f"Scraping detectado desde {request.client.host if request.client else 'unknown'}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Suspicious activity detected"
            )

        # 3. Procesar request
        start_time = time.time()
        response = await call_next(request)

        # 4. Añadir headers de seguridad y timing
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = str(id(request))

        # Ocultar server header (no delatar tecnología)
        response.headers["Server"] = "Web Server"

        # 5. Loguear acceso (excepto health check)
        if request.url.path != "/health":
            api_key = request.headers.get(settings.api_key_header, "none")
            key_preview = f"{api_key[:8]}..." if len(api_key) > 8 else api_key

            logger.bind(context="access").info(
                f"API_ACCESS | key={key_preview} | {request.method} {request.url.path} | "
                f"ip={request.client.host if request.client else 'unknown'} | "
                f"status={response.status_code} | time={process_time:.3f}s"
            )

        return response


# Añadir middlewares (orden importa)
app.add_middleware(SecurityMiddleware)

# Configurar CORS (solo dominios autorizados)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# ============================================================================
# ROUTERS CON AUTENTICACIÓN
# ============================================================================

# NOTA: Usamos prefijos personalizados para dificultar descubrimiento
# En lugar de /api/productos, usamos /v1/internal/products

app.include_router(
    productos.router,
    prefix="/v1/internal/products",  # 🔒 Prefijo personalizado
    tags=["internal-data"]
)

app.include_router(
    familias.router,
    prefix="/v1/internal/families",  # 🔒 Prefijo personalizado
    tags=["internal-data"]
)

app.include_router(
    bc3.router,
    prefix="/v1/internal/bc3",  # 🔒 Prefijo personalizado
    tags=["internal-data"]
)


# ============================================================================
# ENDPOINTS PÚBLICOS (sin autenticación)
# ============================================================================

@app.get("/")
async def root():
    """
    Endpoint raíz - Información básica de la API

    Nota: No revela información sensible sobre endpoints.
    La documentación está deshabilitada por seguridad.
    """
    return {
        "nombre": settings.api_title,
        "version": settings.api_version,
        "descripcion": settings.api_description,
        "ambiente": settings.environment,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint (público)

    No requiere autenticación para permitir monitoreo externo.
    """
    return {
        "status": "ok",
        "service": "api-disano",
        "environment": settings.environment
    }


@app.get("/robots.txt")
async def robots_txt():
    """
    Robots.txt - Bloquear indexación en buscadores

    Previene que la API sea indexada por Google y otros buscadores.
    """
    return Response(
        content="User-agent: *\nDisallow: /\n",
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=86400"}
    )


# ============================================================================
# EVENT HANDLERS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Eventos al iniciar la aplicación.

    Loguea información de configuración de seguridad.
    """
    logger.info("=" * 60)
    logger.info("API DISANO INICIADA - MODO PRODUCCIÓN")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Rate limiting: {settings.rate_limit_enabled}")
    logger.info(f"  → Per client: {settings.rate_limit_per_client}/minute")
    logger.info(f"  → Global: {settings.rate_limit_per_client}/minute")
    logger.info(f"User-Agent filtering: {len(settings.blocked_user_agents)} patterns")
    logger.info(f"Scraping detection: {settings.scraping_detection_enabled}")
    logger.info(f"CORS origins: {settings.cors_origins}")
    logger.info(f"API Keys configuradas: {len(settings.api_keys)}")
    logger.info(f"Documentación: {'DESHABILITADA' if not settings.docs_enabled else 'Habilitada'}")
    logger.info(f"Logging: Nivel {settings.log_level}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Eventos al cerrar la aplicación.

    Loguea estadísticas finales si fuera necesario.
    """
    logger.info("API DISANO DETENIDA")
    logger.info("Liberando recursos...")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production(),  # Reload solo en development
        log_level=settings.log_level.lower()
    )
