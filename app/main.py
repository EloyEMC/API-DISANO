"""
API REST de Disano - Productos y Tarifas
FastAPI con SQLite - VERSIÓN SIMPLIFICADA
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import productos, familias, bc3

# Crear aplicación FastAPI
app = FastAPI(
    title="API Disano",
    description="API REST para consultar productos y tarifas de Disano",
    version="1.0.0",
    docs_url="/docs",  # Habilitado para desarrollo
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(productos.router, prefix="/api/productos", tags=["productos"])
app.include_router(familias.router, prefix="/api/familias", tags=["familias"])
app.include_router(bc3.router, prefix="/api/bc3", tags=["bc3"])

# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz - Información de la API"""
    return {
        "nombre": "API Disano",
        "version": "1.0.0",
        "descripcion": "API REST para consultar productos y tarifas de Disano",
        "endpoints": {
            "productos": "/api/productos",
            "familias": "/api/familias",
            "bc3": "/api/bc3",
            "documentacion": "/docs"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "api-disano"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
