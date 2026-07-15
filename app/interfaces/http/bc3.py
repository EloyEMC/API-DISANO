"""HTTP interface for BC3 using hexagonal architecture

FastAPI router with dependency injection for BC3 endpoints.
Uses existing ProductoService since BC3 data is in ProductoEntity.
."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.domain.services.producto import ProductoService
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
from app.infrastructure.database.connection import SessionLocal
from app.application.dto.producto import ProductoSearchDTO
from app.application.dto.pagination import (
    PaginationRequestDTO,
)

router = APIRouter(prefix="/bc3", tags=["bc3"])


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


# PAGINATED ENDPOINT FIRST (to avoid route conflict)
@router.get("/v2/paginated")
async def buscar_bc3_paginado(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Resultados por página"),
    sort: str = Query(
        None,
        description="Criterio de ordenamiento (ej: codigo:asc, bc3_product_type:desc)",
    ),
    buscar: str = Query(None, description="Término de búsqueda"),
    bc3_product_type: str = Query(
        None, description="Filtrar por tipo de producto BC3 (columna/articulacion)"
    ),
    bc3_has_descripcion_corta: bool = Query(
        None, description="Filtrar productos con descripción corta BC3"
    ),
    bc3_has_descripcion_completa: bool = Query(
        None, description="Filtrar productos con descripción completa BC3"
    ),
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    Buscar productos BC3 con paginación completa V2.

    Endpoint público con soporte completo de paginación, ordenamiento y filtros BC3.
    Proporciona metadatos de paginación y caché integrado.
    ."""
    try:
        # Build pagination request DTO
        pagination_dto = PaginationRequestDTO(
            page=page,
            per_page=per_page,
            sort=sort,
        )

        # Build BC3-specific filters dictionary
        filters = {}
        if buscar:
            filters["buscar"] = buscar
        if bc3_product_type:
            filters["bc3_product_type"] = bc3_product_type
        if bc3_has_descripcion_corta is not None:
            filters["bc3_has_descripcion_corta"] = bc3_has_descripcion_corta
        if bc3_has_descripcion_completa is not None:
            filters["bc3_has_descripcion_completa"] = bc3_has_descripcion_completa

        # Call service method with pagination
        paginated_response = service.buscar_productos_paginado(pagination_dto)

        # Convert entities to dictionaries for filtering
        items_as_dicts = []
        for item in paginated_response.items:
            if hasattr(item, "model_dump"):
                items_as_dicts.append(item.model_dump())
            else:
                items_as_dicts.append(dict(item))

        # Filter results based on BC3 criteria
        filtered_items = []
        for item in items_as_dicts:
            include = True

            # Apply BC3-specific filters
            if bc3_product_type and item.get("bc3_product_type") != bc3_product_type:
                include = False

            if bc3_has_descripcion_corta is not None:
                has_desc = bool(item.get("bc3_descripcion_corta"))
                if has_desc != bc3_has_descripcion_corta:
                    include = False

            if bc3_has_descripcion_completa is not None:
                has_complete = bool(item.get("bc3_descripcion_completa"))
                if has_complete != bc3_has_descripcion_completa:
                    include = False

            if include:
                filtered_items.append(item)

        # Update total count for BC3 filters
        total_bc3_filtered = len(filtered_items)

        # Re-paginate filtered results
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_items = filtered_items[start_idx:end_idx]

        # Convert to response format
        response_dict = {
            "items": paginated_items,
            "pagination": {
                **paginated_response.pagination.model_dump(),
                "total_items": total_bc3_filtered,
                "total_pages": (total_bc3_filtered + per_page - 1) // per_page,
            },
            "filters_applied": {
                **(paginated_response.filters_applied or {}),
                **filters,
            },
            "sorting_applied": paginated_response.sorting_applied,
        }

        return response_dict
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error en búsqueda BC3 paginada: {str(e)}"
        ) from None


@router.get("/v2/stats")
async def get_bc3_stats_v2(
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    Obtener estadísticas BC3 mejoradas V2.

    **V2 New Feature** - Estadísticas BC3 mejoradas con métricas adicionales
    ."""
    try:
        # Get all products to calculate BC3 statistics
        all_products = service.get_all_productos(skip=0, limit=10000)

        total = len(all_products)
        con_descripcion_corta = sum(1 for p in all_products if p.bc3_descripcion_corta)
        con_descripcion_larga = sum(
            1 for p in all_products if p.bc3_descripcion_completa
        )
        con_tipo_producto = sum(1 for p in all_products if p.bc3_product_type)

        # Calculate percentages
        porcentaje_desc_corta = (
            (con_descripcion_corta / total * 100) if total > 0 else 0
        )
        porcentaje_desc_larga = (
            (con_descripcion_larga / total * 100) if total > 0 else 0
        )
        porcentaje_tipo = (con_tipo_producto / total * 100) if total > 0 else 0

        # Count by product type
        tipos = {}
        for p in all_products:
            if p.bc3_product_type:
                tipos[p.bc3_product_type] = tipos.get(p.bc3_product_type, 0) + 1

        return {
            "total": total,
            "con_descripcion_corta": con_descripcion_corta,
            "con_descripcion_larga": con_descripcion_larga,
            "con_tipo_producto": con_tipo_producto,
            "porcentajes": {
                "descripcion_corta": round(porcentaje_desc_corta, 2),
                "descripcion_larga": round(porcentaje_desc_larga, 2),
                "tipo_producto": round(porcentaje_tipo, 2),
            },
            "tipos": tipos,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None


# ============================================
# V1 ENDPOINTS (Backward compatible)
# ============================================


@router.get("/stats")
async def get_bc3_stats(
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    Get BC3 statistics across all products

    **V1 Backward Compatible** - Returns same format as legacy router
    ."""
    try:
        # Get all products to calculate BC3 statistics
        all_products = service.get_all_productos(skip=0, limit=10000)

        total = len(all_products)
        con_descripcion_corta = sum(1 for p in all_products if p.bc3_descripcion_corta)
        con_descripcion_larga = sum(
            1 for p in all_products if p.bc3_descripcion_completa
        )
        con_tipo_producto = sum(1 for p in all_products if p.bc3_product_type)

        return {
            "total": total,
            "con_descripcion_corta": con_descripcion_corta,
            "con_descripcion_larga": con_descripcion_larga,
            "con_tipo_producto": con_tipo_producto,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None


@router.get("/tipo/{tipo}")
async def get_productos_por_tipo_bc3(
    tipo: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum products to return"),
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    Get products by BC3 type (columna or articulacion)

    **V1 Backward Compatible** - Returns same format as legacy router
    ."""
    try:
        # Use bc3_product_type as search term to filter by type
        dto = ProductoSearchDTO(
            buscar=tipo,  # Search in bc3_product_type field
            limit=limit,
            marca="",
            familia="",
        )
        productos = service.buscar_productos(dto)

        return {
            "tipo": tipo,
            "total": len(productos),
            "productos": [p.model_dump() for p in productos],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None


@router.get("/columnas")
async def get_columnas(
    limit: int = Query(10, ge=1, le=100, description="Maximum products to return"),
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    Get all products with bc3_product_type='columna'

    **V1 Backward Compatible** - Returns same format as legacy router
    ."""
    try:
        # Use bc3_product_type='columna' as search term
        dto = ProductoSearchDTO(
            buscar="columna",  # Search for bc3_product_type = 'columna'
            limit=limit,
            marca="",
            familia="",
        )
        productos = service.buscar_productos(dto)

        # Filter to exact matches
        columnas = [p for p in productos if p.bc3_product_type == "columna"]

        return {"total": len(columnas), "productos": [p.model_dump() for p in columnas]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None


@router.get("/articulaciones")
async def get_articulaciones(
    limit: int = Query(10, ge=1, le=100, description="Maximum products to return"),
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    Get all products with bc3_product_type='articulacion'

    **V1 Backward Compatible** - Returns same format as legacy router
    ."""
    try:
        # Use bc3_product_type='articulacion' as search term
        dto = ProductoSearchDTO(
            buscar="articulacion",  # Search for bc3_product_type = 'articulacion'
            limit=limit,
            marca="",
            familia="",
        )
        productos = service.buscar_productos(dto)

        # Filter to exact matches
        articulaciones = [p for p in productos if p.bc3_product_type == "articulacion"]

        return {
            "total": len(articulaciones),
            "productos": [p.model_dump() for p in articulaciones],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None


@router.get("/{codigo}")
async def get_bc3_descripcion(
    codigo: str,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    Get BC3 description for a specific product

    **V1 Backward Compatible** - Returns same format as legacy router
    ."""
    try:
        producto = service.obtener_producto(codigo)

        # Check if product has BC3 data
        if not producto.bc3_descripcion_corta:
            raise HTTPException(
                status_code=404,
                detail=f"Producto {codigo} no encontrado o no tiene datos BC3",
            )

        return {
            "codigo": producto.codigo,
            "descripcion_corta": producto.bc3_descripcion_corta,
            "descripcion_larga": producto.bc3_descripcion_completa,
            "product_type": producto.bc3_product_type,
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Producto {codigo} no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None
