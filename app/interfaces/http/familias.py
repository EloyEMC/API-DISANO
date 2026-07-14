"""HTTP interface for Familia using hexagonal architecture

FastAPI router with dependency injection for families endpoints.
."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from sqlalchemy.orm import Session

from app.domain.services.familia import FamiliaService
from app.infrastructure.repositories.familia import SQLAlchemyFamiliaRepository
from app.infrastructure.database.connection import SessionLocal
from app.application.dto.pagination import (
    PaginationRequestDTO,
)
from app.interfaces.http.response_serializers import FamiliaResponseSerializer


router = APIRouter(prefix="/familias", tags=["familias"])


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


def get_familia_service(session: Session = Depends(get_db_session)) -> FamiliaService:
    """DI function to create FamiliaService with repository."""
    return FamiliaService(SQLAlchemyFamiliaRepository(session))


# ============================================
# V2 ENDPOINTS (Públicos, sin autenticación)
# ============================================


# PAGINATED ENDPOINT FIRST (to avoid route conflict)
@router.get("/v2/paginated")
async def buscar_familias_paginado(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Resultados por página"),
    sort: str = Query(
        None,
        description="Criterio de ordenamiento (ej: nombre:asc, total_productos:desc)",
    ),
    buscar: str = Query(None, description="Término de búsqueda"),
    service: FamiliaService = Depends(get_familia_service),
) -> dict:
    """
    Buscar familias con paginación completa V2.

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

        # Call service method with pagination
        paginated_response = service.buscar_familias_paginado(pagination_dto)

        # Serialize response using FamiliaResponseSerializer
        response_dict = FamiliaResponseSerializer.serialize_paginated_response(
            paginated_response, "familia"
        )

        return response_dict
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error en búsqueda paginada: {str(e)}"
        ) from None


@router.get("/v2/top-bc3")
async def get_top_bc3_coverage_v2(
    limit: int = Query(5, ge=1, le=10, description="Número de familias principales"),
    service: FamiliaService = Depends(get_familia_service),
) -> list:
    """
    Obtener familias con mayor cobertura BC3 V2.

    **V2 New Feature** - Endpoint mejorado con funcionalidad adicional
    ."""
    try:
        leaderboard = service.get_bc3_coverage_leaderboard(limit=limit)
        return [
            {
                **familia.model_dump(),
                "bc3_coverage_percentage": familia.get_bc3_coverage_percentage(),
            }
            for familia in leaderboard
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None


# ============================================
# V1 ENDPOINTS (Backward compatible)
# ============================================


@router.get("/")
async def get_familias(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of families"),
    service: FamiliaService = Depends(get_familia_service),
) -> List:
    """
    Get all families with BC3 statistics

    **V1 Backward Compatible** - Returns same format as legacy router
    ."""
    try:
        familias = service.get_all_familias()
        return [familia.model_dump() for familia in familias[:limit]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None


@router.get("/stats")
async def get_familias_stats(
    service: FamiliaService = Depends(get_familia_service),
) -> dict:
    """
    Get aggregate statistics across all families

    **V1 Backward Compatible** - Returns same format as legacy router
    ."""
    try:
        stats = service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None


@router.get("/{nombre}")
async def get_familia_by_nombre(
    nombre: str,
    service: FamiliaService = Depends(get_familia_service),
) -> dict:
    """
    Get family by name with statistics

    **V1 Backward Compatible** - Returns same format as legacy router
    ."""
    try:
        familia = service.get_familia_by_nombre(nombre)
        return familia.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None


@router.get("/top-bc3")
async def get_top_bc3_coverage(
    limit: int = Query(5, ge=1, le=10, description="Number of top families"),
    service: FamiliaService = Depends(get_familia_service),
) -> List:
    """
    Get families with highest BC3 coverage

    **V2 New Feature** - New endpoint with enhanced functionality
    ."""
    try:
        leaderboard = service.get_bc3_coverage_leaderboard(limit=limit)
        return [
            {
                **familia.model_dump(),
                "bc3_coverage_percentage": familia.get_bc3_coverage_percentage(),
            }
            for familia in leaderboard
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None
