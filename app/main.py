"""
API REST de Disano - Productos y Tarifas
FastAPI con SQLite - CON SEGURIDAD
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import productos, familias, bc3
from app.security import (
    APIKeyMiddleware,
    RateLimitMiddleware,
    UserAgentMiddleware,
    SecurityHeadersMiddleware
)
import os

# Load environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Crear aplicación FastAPI
# Documentation is DISABLED in production
app = FastAPI(
    title="API Disano",
    description="API REST para consultar productos y tarifas de Disano",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
    openapi_url="/openapi.json" if ENVIRONMENT == "development" else None
)

# Configure CORS based on environment
if ENVIRONMENT == "production":
    # In production: restrict CORS to specific domains
    allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
    if not allowed_origins or allowed_origins == [""]:
        allowed_origins = ["https://eloymartinezcuesta.com"]
else:
    # In development: allow all origins
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
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

# Incluir routers
app.include_router(productos.router, prefix="/api/productos", tags=["productos"])
app.include_router(familias.router, prefix="/api/familias", tags=["familias"])
app.include_router(bc3.router, prefix="/api/bc3", tags=["bc3"])

# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz - Información de la API"""
    endpoints = {
        "productos": "/api/productos",
        "familias": "/api/familias",
        "bc3": "/api/bc3"
    }

    # Only show docs in development
    if ENVIRONMENT == "development":
        endpoints["documentacion"] = "/docs"

    return {
        "nombre": "API Disano",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "descripcion": "API REST para consultar productos y tarifas de Disano",
        "endpoints": endpoints
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "api-disano"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
