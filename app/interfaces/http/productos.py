"""HTTP interface for Productos using hexagonal architecture

FastAPI router with dependency injection for product endpoints.
."""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.domain.services.producto import ProductoService
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
from app.infrastructure.database.connection import SessionLocal
from app.application.dto.pagination import (
    PaginationRequestDTO,
)
from app.interfaces.http.response_serializers import ProductoResponseSerializer


# ============================================
# REQUEST MODELS
# ============================================


class BuscarProductosRequest(BaseModel):
    """Request model for POST /buscar-productos endpoint.

    Compatible with BC3-Suite frontend JSON payload.
    """

    termino: Optional[str] = None
    limit: int = 20
    marca: Optional[str] = None
    familia: Optional[str] = None
    con_bc3: bool = False

    class Config:
        extra = "forbid"  # Reject unexpected fields


router = APIRouter(prefix="/productos", tags=["productos"])


# ============================================
# DEPENDENCY INJECTION FUNCTIONS
# ============================================


def get_db_session() -> Session:
    """DI function to get database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_producto_service(session: Session = Depends(get_db_session)) -> ProductoService:
    """DI function to create ProductoService with repository."""
    return ProductoService(SQLAlchemyProductoRepository(session))


# ============================================
# V2 ENDPOINTS (Públicos, sin autenticación)
# ============================================


# POST ENDPOINT FOR FRONTEND COMPATIBILITY
@router.post("/buscar-productos")
async def buscar_productos_post(
    request: BuscarProductosRequest,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    POST endpoint for product search (BC3-Suite frontend compatibility).

    Wrapper of /v2/paginated that accepts JSON body.
    Maps frontend parameters → backend V2 format.
    Returns response in frontend-expected format.

    **Frontend Compatibility**:
    - Accepts: {"termino": "toledo", "limit": 20, "marca": "", "familia": ""}
    - Returns: {"status": "success", "resultados": [...], "count": N, "total": M}

    **Backend Reuse**:
    - Calls: ProductoService.buscar_productos_paginado()
    - Uses: ProductoResponseSerializer.serialize_paginated_response()
    """
    try:
        # Map frontend parameters → backend V2 format
        filters = {}
        if request.termino:
            filters["buscar"] = request.termino
        if request.marca:
            filters["marca"] = request.marca
        if request.familia:
            filters["familia"] = request.familia
        if request.con_bc3:
            # Filter by BC3 product types
            filters["bc3_product_type"] = "luminaria"

        # Build pagination DTO (always page 1 for frontend search)
        pagination_dto = PaginationRequestDTO(
            page=1,
            per_page=min(request.limit, 100),  # Cap at 100
        )

        # Call service with pagination and filters
        paginated_response = service.buscar_productos_paginado(
            pagination_dto, filters
        )

        # Serialize response using ProductoResponseSerializer
        response_dict = ProductoResponseSerializer.serialize_paginated_response(
            paginated_response, "producto"
        )

        # Map backend response → frontend-expected format
        frontend_response = {
            "status": "success",
            "resultados": response_dict.get("items", []),
            "count": len(response_dict.get("items", [])),
            "total": response_dict.get("total", 0),
        }

        return frontend_response

    except Exception as e:
        # Return error in frontend-expected format
        return {
            "status": "error",
            "resultados": [],
            "count": 0,
            "total": 0,
            "error": str(e),
}


# PAGINATED ENDPOINT FIRST (to avoid route conflict)
@router.get("/v2/paginated")
async def buscar_productos_paginado(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Resultados por página"),
    sort: str = Query(
        None, description="Criterio de ordenamiento (ej: codigo:asc, pvp:desc)"
    ),
    buscar: str = Query(None, description="Término de búsqueda"),
    marca: str = Query(None, description="Filtrar por marca"),
    familia: str = Query(None, description="Filtrar por familia"),
    pvp_min: float = Query(None, ge=0, description="Precio mínimo"),
    pvp_max: float = Query(None, ge=0, description="Precio máximo"),
    bc3_product_type: str = Query(None, description="Tipo de producto BC3"),
    bc3_has_descripcion_corta: bool = Query(
        None, description="Filtrar por descripción corta BC3"
    ),
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    Buscar productos con paginación completa V2.

    Endpoint público con soporte completo de paginación, ordenamiento y filtros.
    Proporciona metadatos de paginación y caché integrado.
    ."""
    try:
        # Build pagination request DTO
        pagination_dto = PaginationRequestDTO(
            page=page,
            per_page=per_page,
            sort=sort,
        )

        # Build filters dictionary
        filters = {}
        if buscar:
            filters["buscar"] = buscar
        if marca:
            filters["marca"] = marca
        if familia:
            filters["familia"] = familia
        if pvp_min is not None:
            filters["pvp_min"] = pvp_min
        if pvp_max is not None:
            filters["pvp_max"] = pvp_max
        if bc3_product_type:
            filters["bc3_product_type"] = bc3_product_type
        if bc3_has_descripcion_corta is not None:
            filters["bc3_has_descripcion_corta"] = bc3_has_descripcion_corta

        # Call service method with pagination
        paginated_response = service.buscar_productos_paginado(pagination_dto, filters)

        # Serialize response using ProductoResponseSerializer
        response_dict = ProductoResponseSerializer.serialize_paginated_response(
            paginated_response, "producto"
        )

        return response_dict
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error en búsqueda paginada: {str(e)}"
        ) from None


# V2 LIST ENDPOINT (Backward compatibility with tests)
@router.get("/v2/list")
async def buscar_productos_list_v2(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(
        20, ge=1, le=100, description="Resultados por página (alias de per_page)"
    ),
    sort: str = Query(
        None, description="Criterio de ordenamiento (ej: codigo:asc, pvp:desc)"
    ),
    buscar: str = Query(None, description="Término de búsqueda"),
    marca: str = Query(None, description="Filtrar por marca"),
    familia: str = Query(None, description="Filtrar por familia"),
    pvp_min: float = Query(None, ge=0, description="Precio mínimo"),
    pvp_max: float = Query(None, ge=0, description="Precio máximo"),
    bc3_product_type: str = Query(None, description="Tipo de producto BC3"),
    bc3_has_descripcion_corta: bool = Query(
        None, description="Filtrar por descripción corta BC3"
    ),
    service: ProductoService = Depends(get_producto_service),
) -> list:
    """
    Buscar productos V2 (compatibilidad con tests).

    Alias de /v2/paginated que devuelve solo items (sin metadata).
    Mapea 'limit' → 'per_page' para compatibilidad.
    ."""
    try:
        pagination_dto = PaginationRequestDTO(
            page=page,
            per_page=limit,  # Map limit to per_page
            sort=sort,
        )

        filters = {}
        if buscar:
            filters["buscar"] = buscar
        if marca:
            filters["marca"] = marca
        if familia:
            filters["familia"] = familia
        if pvp_min is not None:
            filters["pvp_min"] = pvp_min
        if pvp_max is not None:
            filters["pvp_max"] = pvp_max
        if bc3_product_type:
            filters["bc3_product_type"] = bc3_product_type
        if bc3_has_descripcion_corta is not None:
            filters["bc3_has_descripcion_corta"] = bc3_has_descripcion_corta

        paginated_response = service.buscar_productos_paginado(pagination_dto, filters)
        response_dict = ProductoResponseSerializer.serialize_paginated_response(
            paginated_response, "producto"
        )

        return response_dict.get("items", [])
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error en búsqueda: {str(e)}"
        ) from None


# ============================================
# V1 ENDPOINTS (Backward compatible)
# ============================================


@router.get("/")
async def get_productos(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of products"),
    service: ProductoService = Depends(get_producto_service),
) -> List:
    """
    Get all products with BC3 statistics

    **V1 Backward Compatible** - Returns same format as legacy router
    ."""
    try:
        productos = service.get_all_productos()
        return [producto.model_dump() for producto in productos[:limit]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None


@router.get("/{codigo}")
async def get_producto(
    codigo: str,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    Get product by code with BC3 details

    **V1 Backward Compatible** - Returns same format as legacy router
    ."""
    try:
        producto = service.obtener_producto(codigo)
        return producto.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None
