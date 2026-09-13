"""HTTP interface for Productos using hexagonal architecture.

FastAPI router with dependency injection for product endpoints.
"""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.dto.bc3_enrichment import (
    BC3EnrichmentApplyRequest,
    BC3EnrichmentApplyResponse,
    BC3EnrichmentApprovalRequest,
    BC3EnrichmentApprovalResponse,
    BC3EnrichmentJobStatusResponse,
    BC3EnrichmentPreviewRequest,
    BC3EnrichmentPreviewResponse,
)
from app.application.dto.pagination import (
    PaginationRequestDTO,
)
from app.application.dto.producto import (
    ProductoBC3Page,
    ProductoBC3Response,
    ProductoExternalPage,
    ProductoExternalResponse,
)
from app.application.services.github_approval import (
    GitHubApprovalUnavailable,
    GitHubApprovalVerifier,
)
from app.config import get_settings
from app.domain.exceptions.not_found import ProductoNotFoundException
from app.domain.services.producto import ProductoService
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
from app.interfaces.http.response_serializers import ProductoResponseSerializer

_bc3_api_key = APIKeyHeader(
    name=get_settings().api_key_header,
    description="API key for private BC3 access",
    auto_error=False,
)


async def verify_bc3_api_key(api_key: str | None = Depends(_bc3_api_key)) -> str:
    """Validate the private BC3 credential without exposing its value."""
    if api_key is None or api_key not in get_settings().bc3_api_keys_list:
        raise HTTPException(status_code=401, detail="API Key inválida")
    return api_key


# ============================================
# REQUEST MODELS
# ============================================


class BuscarProductosRequest(BaseModel):
    """Request model for POST /buscar-productos endpoint.

    Compatible with BC3-Suite frontend JSON payload.
    """

    termino: str | None = None
    limit: int = 20
    marca: str | None = None
    familia: str | None = None
    con_bc3: bool = False

    class Config:
        """Configure request validation."""

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
    """DI function to create ProductoService with repository and verifier."""
    settings = get_settings()
    verifier = GitHubApprovalVerifier(
        # Keep ordinary service construction compatible with lightweight test settings;
        # missing approval configuration still fails closed when approval is attempted.
        token=getattr(settings, "github_api_token", None),
        expected_repository=getattr(settings, "github_expected_repository", None),
        api_base_url=getattr(settings, "github_api_url", "https://api.github.com"),
        required_approvals=getattr(settings, "github_required_approvals", 1),
        approval_mode=getattr(settings, "bc3_approval_mode", "github_review"),
    )
    return ProductoService(SQLAlchemyProductoRepository(session), verifier)


def _contract_item(entity: Any) -> dict:
    """Project a domain entity into the explicit public contract."""
    data = entity.model_dump() if hasattr(entity, "model_dump") else dict(entity)
    return ProductoExternalResponse.model_validate(data).model_dump(exclude_none=True)


def _public_filters(buscar: str | None, marca: str | None, familia: str | None) -> dict:
    return {
        key: value
        for key, value in {
            "buscar": buscar,
            "marca": marca,
            "familia": familia,
        }.items()
        if value
    }


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
        paginated_response = service.buscar_productos_paginado(pagination_dto, filters)

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


async def _list_public_contract(
    service: ProductoService,
    page: int,
    per_page: int,
    buscar: str | None,
    marca: str | None,
    familia: str | None,
) -> dict:
    filters = _public_filters(buscar, marca, familia)
    response = service.buscar_productos_paginado(
        PaginationRequestDTO(page=page, per_page=per_page, sort=None), filters
    )
    return {
        "items": [_contract_item(item) for item in response.items],
        "pagination": response.pagination.model_dump(),
        "filters_applied": filters,
        "sorting_applied": response.sorting_applied,
    }


@router.get(
    "/v1",
    response_model=ProductoExternalPage,
    summary="List public products (v1)",
)
async def list_products_v1(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    buscar: str | None = None,
    marca: str | None = None,
    familia: str | None = None,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """Return the stable external product contract."""
    return await _list_public_contract(service, page, per_page, buscar, marca, familia)


@router.get(
    "/v1/{codigo}",
    response_model=ProductoExternalResponse,
    summary="Get one public product",
)
async def get_product_v1(
    codigo: str, service: ProductoService = Depends(get_producto_service)
) -> dict:
    """Return one product in the external contract."""
    try:
        return _contract_item(service.obtener_producto(codigo))
    except ProductoNotFoundException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get(
    "/bc3/v1",
    response_model=ProductoBC3Page,
    dependencies=[Depends(verify_bc3_api_key)],
    summary="List products for BC3",
)
async def list_products_bc3_v1(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    buscar: str | None = None,
    marca: str | None = None,
    familia: str | None = None,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """Return the private BC3 product contract."""
    filters = _public_filters(buscar, marca, familia)
    response = service.buscar_productos_privado(
        PaginationRequestDTO(page=page, per_page=per_page, sort=None), filters
    )
    return {
        "items": [
            ProductoBC3Response.model_validate(item.model_dump()).model_dump(exclude_none=True)
            for item in response.items
        ],
        "pagination": response.pagination.model_dump(),
        "filters_applied": filters,
        "sorting_applied": response.sorting_applied,
    }


@router.get(
    "/bc3/v1/{codigo}",
    response_model=ProductoBC3Response,
    dependencies=[Depends(verify_bc3_api_key)],
    summary="Get one product for BC3",
)
async def get_product_bc3_v1(
    codigo: str, service: ProductoService = Depends(get_producto_service)
) -> dict:
    """Return one product in the private BC3 contract."""
    try:
        entity = service.obtener_producto_privado(codigo)
        return ProductoBC3Response.model_validate(entity.model_dump()).model_dump(exclude_none=True)
    except ProductoNotFoundException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.post(
    "/bc3/v1/enrichment/preview",
    response_model=BC3EnrichmentPreviewResponse,
    dependencies=[Depends(verify_bc3_api_key)],
    summary="Preview BC3 enrichment changes",
)
async def preview_bc3_enrichment(
    request: BC3EnrichmentPreviewRequest,
    actor_id: str = Header(..., alias="X-BC3-Actor", min_length=1),
    service: ProductoService = Depends(get_producto_service),
) -> BC3EnrichmentPreviewResponse:
    """Create a durable, read-only preview snapshot."""
    return service.preview_bc3_enrichment(request, actor_id)


@router.post(
    "/bc3/v1/enrichment/approve",
    response_model=BC3EnrichmentApprovalResponse,
    dependencies=[Depends(verify_bc3_api_key)],
    summary="Explicitly approve a BC3 enrichment preview",
)
async def approve_bc3_enrichment(
    request: BC3EnrichmentApprovalRequest,
    actor_id: str = Header(..., alias="X-BC3-Actor", min_length=1),
    approval_key: str | None = Header(None, alias="X-BC3-Approval-Key"),
    service: ProductoService = Depends(get_producto_service),
) -> BC3EnrichmentApprovalResponse:
    """Approve a BC3 enrichment preview."""
    settings = get_settings()
    if not settings.bc3_approval_keys_list or approval_key not in settings.bc3_approval_keys_list:
        raise HTTPException(status_code=403, detail="Dedicated BC3 approval credential required")
    try:
        evidence = service.approve_bc3_preview(
            request.preview_id,
            actor_id,
            settings.bc3_approval_scope,
            request.github_pr,
        )
    except GitHubApprovalUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return BC3EnrichmentApprovalResponse(
        preview_id=request.preview_id,
        status="approved",
        github_pr=request.github_pr,
        github_approval_count=evidence.approval_count,
        github_approval_mode=evidence.approval_mode,
    )


@router.post(
    "/bc3/v1/enrichment/apply",
    response_model=BC3EnrichmentApplyResponse,
    dependencies=[Depends(verify_bc3_api_key)],
    summary="Apply BC3 enrichment changes",
)
async def apply_bc3_enrichment(
    request: BC3EnrichmentApplyRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1),
    actor_id: str = Header(..., alias="X-BC3-Actor", min_length=1),
    approval_key: str | None = Header(None, alias="X-BC3-Approval-Key"),
    service: ProductoService = Depends(get_producto_service),
) -> BC3EnrichmentApplyResponse:
    """Apply BC3 enrichment atomically with durable idempotency."""
    settings = get_settings()
    if not settings.bc3_approval_keys_list or approval_key not in settings.bc3_approval_keys_list:
        raise HTTPException(status_code=403, detail="Dedicated BC3 approval credential required")
    try:
        return service.apply_bc3_enrichment(request, idempotency_key, actor_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get(
    "/bc3/v1/enrichment/jobs/{job_id}",
    response_model=BC3EnrichmentJobStatusResponse,
    dependencies=[Depends(verify_bc3_api_key)],
    summary="Get BC3 enrichment job status",
)
async def get_bc3_enrichment_job_status(
    job_id: str, service: ProductoService = Depends(get_producto_service)
) -> BC3EnrichmentJobStatusResponse:
    """Return a safe read-only status projection for an enrichment job."""
    result = service.obtener_estado_enriquecimiento_bc3(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Enrichment job not found")
    safe_result = {
        field: result[field]
        for field in (
            "job_id",
            "status",
            "total_items",
            "updated_items",
            "unchanged_items",
            "missing_items",
            "created_at",
            "completed_at",
        )
    }
    safe_result["items"] = [
        {field: item[field] for field in ("codigo", "result_status", "error_message")}
        for item in sorted(result["items"], key=lambda item: item["codigo"])
    ]
    return BC3EnrichmentJobStatusResponse.model_validate(safe_result)


@router.get(
    "/v3",
    response_model=ProductoExternalPage,
    summary="List public products",
)
async def list_products_v3(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    buscar: str | None = None,
    marca: str | None = None,
    familia: str | None = None,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """Compatibility alias for the stable external product contract."""
    return await _list_public_contract(service, page, per_page, buscar, marca, familia)


# PAGINATED ENDPOINT FIRST (to avoid route conflict)
@router.get("/v2/paginated")
async def buscar_productos_paginado(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Resultados por página"),
    sort: str = Query(None, description="Criterio de ordenamiento (ej: codigo:asc, pvp:desc)"),
    buscar: str = Query(None, description="Término de búsqueda"),
    marca: str = Query(None, description="Filtrar por marca"),
    familia: str = Query(None, description="Filtrar por familia"),
    pvp_min: float = Query(None, ge=0, description="Precio mínimo"),
    pvp_max: float = Query(None, ge=0, description="Precio máximo"),
    bc3_product_type: str = Query(None, description="Tipo de producto BC3"),
    bc3_has_descripcion_corta: bool = Query(None, description="Filtrar por descripción corta BC3"),
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    Buscar productos con paginación completa V2.

    Endpoint público con soporte completo de paginación, ordenamiento y filtros.
    Proporciona metadatos de paginación y caché integrado.
    """
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
    limit: int = Query(20, ge=1, le=100, description="Resultados por página (alias de per_page)"),
    sort: str = Query(None, description="Criterio de ordenamiento (ej: codigo:asc, pvp:desc)"),
    buscar: str = Query(None, description="Término de búsqueda"),
    marca: str = Query(None, description="Filtrar por marca"),
    familia: str = Query(None, description="Filtrar por familia"),
    pvp_min: float = Query(None, ge=0, description="Precio mínimo"),
    pvp_max: float = Query(None, ge=0, description="Precio máximo"),
    bc3_product_type: str = Query(None, description="Tipo de producto BC3"),
    bc3_has_descripcion_corta: bool = Query(None, description="Filtrar por descripción corta BC3"),
    service: ProductoService = Depends(get_producto_service),
) -> list:
    """
    Buscar productos V2 (compatibilidad con tests).

    Alias de /v2/paginated que devuelve solo items (sin metadata).
    Mapea 'limit' → 'per_page' para compatibilidad.
    """
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
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}") from None


# ============================================
# V1 ENDPOINTS (Backward compatible)
# ============================================


@router.get("/")
async def get_productos(
    response: Response,
    page: int = Query(1, ge=1, description="1-based page number"),
    limit: int | None = Query(None, ge=1, le=500, description="Items per page (legacy alias)"),
    per_page: int | None = Query(None, ge=1, le=500, description="Items per page"),
    service: ProductoService = Depends(get_producto_service),
) -> list:
    """Return one stable, backward-compatible page of products.

    The JSON body remains the legacy ``list[dict]`` contract. Pagination totals
    are exposed in headers so existing consumers do not need to change their
    decoder: ``X-Total`` and ``X-Total-Pages``. Use ``per_page`` or its legacy
    ``limit`` alias, but not both.
    """
    if limit is not None and per_page is not None:
        raise HTTPException(
            status_code=422,
            detail="Use only one of the pagination parameters: limit or per_page",
        )

    page_size = per_page if per_page is not None else limit or 50
    skip = (page - 1) * page_size

    try:
        productos = service.get_all_productos(skip=skip, limit=page_size)
        total = service.count_productos()
        total_pages = (total + page_size - 1) // page_size
        response.headers["X-Total"] = str(total)
        response.headers["X-Total-Pages"] = str(total_pages)
        response.headers["X-Page"] = str(page)
        response.headers["X-Per-Page"] = str(page_size)
        return [producto.model_dump() for producto in productos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None


@router.get("/{codigo}")
async def get_producto(
    codigo: str,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """
    Get product by code with BC3 details.

    **V1 Backward Compatible** - Returns same format as legacy router
    """
    try:
        producto = service.obtener_producto(codigo)
        return producto.model_dump()
    except (ProductoNotFoundException, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") from None
