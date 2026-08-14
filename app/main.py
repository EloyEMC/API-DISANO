"""API REST de Disano - Productos y Tarifas.

FastAPI service with secure runtime configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.interfaces.http import (
    productos as productos_http,
    familias as familias_http,
    bc3 as bc3_http,
)
from app.middleware import (
    APIKeyMiddleware,
    RateLimitMiddleware,
    UserAgentMiddleware,
    SecurityHeadersMiddleware,
)
from app.interfaces.http.error_handlers import register_exception_handlers
from app.security.logging_config import setup_logging
from app.config import get_settings

settings = get_settings()
setup_logging()

# Load environment
ENVIRONMENT = settings.environment


def validate_startup_configuration() -> None:
    """Fail closed for invalid production secrets without restricting local modes."""
    get_settings().validate_required()


validate_startup_configuration()

DOCS_ENABLED = bool(settings.docs_enabled)

# Crear aplicación FastAPI
app = FastAPI(
    title="API Disano",
    description="API REST para consultar productos y tarifas de Disano",
    version="1.0.0",
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)

# Configure CORS based on environment
if ENVIRONMENT == "production":
    # In production: restrict CORS to specific domains
    allowed_origins = settings.cors_origins_list
    if not allowed_origins or allowed_origins == [""]:
        allowed_origins = ["https://eloymartinezcuesta.com"]
else:
    # In development: allow configured origins, defaulting to all origins.
    allowed_origins = settings.cors_origins_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=settings.cors_allow_credentials and "*" not in allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middlewares
app.add_middleware(SecurityHeadersMiddleware)

# Only add these in production
if ENVIRONMENT == "production":
    app.add_middleware(APIKeyMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(UserAgentMiddleware)

# Incluir routers (hexagonal architecture)
app.include_router(productos_http.router, prefix="/api", tags=["productos"])
app.include_router(familias_http.router, prefix="/api", tags=["familias"])
app.include_router(bc3_http.router, prefix="/api", tags=["bc3"])

# Registrar manejadores de excepciones V2
register_exception_handlers(app)


# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz - Información de la API."""
    endpoints = {
        "productos": "/api/productos",
        "familias": "/api/familias",
        "bc3": "/api/bc3",
    }

    if DOCS_ENABLED:
        endpoints["documentacion"] = "/docs"

    return {
        "nombre": "API Disano",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "descripcion": "API REST para consultar productos y tarifas de Disano",
        "endpoints": endpoints,
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "api-disano"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
