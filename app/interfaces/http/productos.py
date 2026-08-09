"""Typed product HTTP contracts with legacy compatibility."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.dto.bc3_enrichment import (
    BC3EnrichmentApplyRequest,
    BC3EnrichmentApplyResponse,
    BC3EnrichmentJobStatusResponse,
    BC3EnrichmentPreviewItem,
    BC3EnrichmentPreviewRequest,
    BC3EnrichmentPreviewResponse,
    hash_bc3_enrichment_items,
)
from app.application.dto.pagination import PaginationRequestDTO
from app.application.dto.producto import (
    ProductoBC3Page,
    ProductoBC3Response,
    ProductoExternalPage,
    ProductoExternalResponse,
)
from app.domain.exceptions.not_found import ProductoNotFoundException
from app.domain.services.producto import ProductoService
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
from app.config import get_settings
from app.security.api_key import verify_admin_api_key
from app.security.api_key import require_admin_api_key
from app.interfaces.http.response_serializers import ProductoResponseSerializer


_bc3_api_key = APIKeyHeader(
    name=get_settings().api_key_header, description="API key for private BC3 access"
)


async def verify_bc3_api_key(api_key: str = Depends(_bc3_api_key)) -> str:
    """Validate the private BC3 credential without exposing its value."""
    if api_key not in get_settings().bc3_api_keys_list:
        raise HTTPException(status_code=401, detail="API Key inválida")
    return api_key


class BuscarProductosRequest(BaseModel):
    """Legacy BC3-Suite search payload."""

    termino: Optional[str] = None
    limit: int = Query(20, ge=1, le=100)
    marca: Optional[str] = None
    familia: Optional[str] = None
    con_bc3: bool = False


router = APIRouter(prefix="/productos", tags=["productos"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


def get_db_session():
    """Yield a transactional database session for the request."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_producto_service(session: Session = Depends(get_db_session)) -> ProductoService:
    """Build the product service with its repository adapter."""
    return ProductoService(SQLAlchemyProductoRepository(session))


def _contract_item(entity: Any, private: bool) -> dict:
    """Project a domain entity into the selected explicit contract."""
    data = entity.model_dump() if hasattr(entity, "model_dump") else dict(entity)
    schema = ProductoBC3Response if private else ProductoExternalResponse
    return schema.model_validate(data).model_dump(exclude_none=True)


def _filters(buscar: Optional[str], marca: Optional[str], familia: Optional[str]) -> dict:
    """Filter product query parameters."""
    return {
        key: value
        for key, value in {"buscar": buscar, "marca": marca, "familia": familia}.items()
        if value
    }


@router.post("/buscar-productos")
async def buscar_productos_post(
    request: BuscarProductosRequest,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """Legacy frontend-compatible search response."""
    filters = _filters(request.termino, request.marca, request.familia)
    if request.con_bc3:
        filters["bc3_product_type"] = "luminaria"
    response = service.buscar_productos_paginado(
        PaginationRequestDTO(page=1, per_page=request.limit, sort=None), filters
    )
    serialized = ProductoResponseSerializer.serialize_paginated_response(response)
    return {
        "status": "success",
        "resultados": serialized["items"],
        "count": len(serialized["items"]),
        "total": serialized["pagination"].get("total_items", 0),
    }


async def _list_contract(
    service: ProductoService,
    page: int,
    per_page: int,
    buscar: Optional[str],
    marca: Optional[str],
    familia: Optional[str],
    private: bool,
) -> dict:
    """List contract."""
    filters = _filters(buscar, marca, familia)
    response = (
        service.buscar_productos_privado(
            PaginationRequestDTO(page=page, per_page=per_page, sort=None), filters
        )
        if private
        else service.buscar_productos_paginado(
            PaginationRequestDTO(page=page, per_page=per_page, sort=None), filters
        )
    )
    return {
        "items": [_contract_item(item, private) for item in response.items],
        "pagination": response.pagination.model_dump(),
        "filters_applied": filters,
        "sorting_applied": response.sorting_applied,
    }


@router.get(
    "/v1",
    response_model=ProductoExternalPage,
    summary="List public products (v1)",
    description="Public client contract; discounts and logistics are excluded.",
)
async def list_products_v1(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    buscar: Optional[str] = None,
    marca: Optional[str] = None,
    familia: Optional[str] = None,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """Return the stable external product contract."""
    return await _list_contract(service, page, per_page, buscar, marca, familia, False)


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
        return _contract_item(service.obtener_producto(codigo), private=False)
    except ProductoNotFoundException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get(
    "/v3",
    response_model=ProductoExternalPage,
    summary="List public products",
    description="Public client contract; discounts and logistics are excluded.",
)
async def list_products_v3(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    buscar: Optional[str] = None,
    marca: Optional[str] = None,
    familia: Optional[str] = None,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """Return the stable external product contract."""
    return await _list_contract(service, page, per_page, buscar, marca, familia, False)


@router.get(
    "/bc3/v1",
    response_model=ProductoBC3Page,
    dependencies=[Depends(verify_bc3_api_key)],
    summary="List products for BC3",
    description="Private BC3 contract; requires the X-API-Key header.",
)
async def list_products_bc3_v1(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    buscar: Optional[str] = None,
    marca: Optional[str] = None,
    familia: Optional[str] = None,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """Return the private BC3 product contract."""
    return await _list_contract(service, page, per_page, buscar, marca, familia, True)


@router.post(
    "/bc3/v1/enrichment/preview",
    response_model=BC3EnrichmentPreviewResponse,
    dependencies=[Depends(verify_bc3_api_key)],
    summary="Preview BC3 enrichment changes",
    description="Read-only private BC3 enrichment preview; no catalog fields are persisted.",
)
async def preview_bc3_enrichment(
    request: BC3EnrichmentPreviewRequest,
    service: ProductoService = Depends(get_producto_service),
) -> BC3EnrichmentPreviewResponse:
    """Return proposed BC3 field changes without writing to the catalog."""
    items, missing_codes = service.preview_bc3_enrichment(
        [item.model_dump() for item in request.items]
    )
    return BC3EnrichmentPreviewResponse(
        items=[BC3EnrichmentPreviewItem.model_validate(item) for item in items],
        missing_codes=missing_codes,
    )


@router.post(
    "/bc3/v1/enrichment/apply",
    response_model=BC3EnrichmentApplyResponse,
    dependencies=[Depends(verify_bc3_api_key)],
    summary="Apply BC3 enrichment changes",
    description="Transactional private BC3 enrichment for the four whitelisted descriptive fields.",
)
async def apply_bc3_enrichment(
    request: BC3EnrichmentApplyRequest,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=200,
        description="Client-generated key for safe replay of this exact payload.",
    ),
    service: ProductoService = Depends(get_producto_service),
) -> BC3EnrichmentApplyResponse:
    """Persist a complete, validated BC3 batch through the durable job record."""
    items = [item.model_dump() for item in request.items]
    try:
        result = service.apply_bc3_enrichment(
            items,
            idempotency_key=idempotency_key,
            request_hash=hash_bc3_enrichment_items(items),
        )
    except ProductoNotFoundException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    status = result.get("status")
    if status == "idempotency_conflict":
        raise HTTPException(
            status_code=409,
            detail="Idempotency-Key was already used for a different request",
        )
    if status == "job_in_progress":
        raise HTTPException(status_code=409, detail="Enrichment job is already in progress")
    return BC3EnrichmentApplyResponse.model_validate(result)


@router.get(
    "/bc3/v1/enrichment/jobs/{job_id}",
    response_model=BC3EnrichmentJobStatusResponse,
    dependencies=[Depends(verify_bc3_api_key)],
    summary="Get BC3 enrichment job status",
    description="Read-only durable BC3 enrichment status; asynchronous execution is not active.",
)
async def get_bc3_enrichment_job_status(
    job_id: str, service: ProductoService = Depends(get_producto_service)
) -> BC3EnrichmentJobStatusResponse:
    """Return a safe status projection for a previously applied BC3 job."""
    result = service.obtener_estado_enriquecimiento_bc3(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Enrichment job not found")
    return BC3EnrichmentJobStatusResponse.model_validate(result)


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
        return _contract_item(service.obtener_producto_privado(codigo), private=True)
    except ProductoNotFoundException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None


@router.get("/v2/paginated")
async def buscar_productos_paginado(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort: Optional[str] = None,
    buscar: Optional[str] = None,
    marca: Optional[str] = None,
    familia: Optional[str] = None,
    pvp_min: Optional[float] = Query(None, ge=0),
    pvp_max: Optional[float] = Query(None, ge=0),
    bc3_product_type: Optional[str] = None,
    bc3_has_descripcion_corta: Optional[bool] = None,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """Legacy V2 paginated response."""
    filters = _filters(buscar, marca, familia)
    for key, value in {
        "pvp_min": pvp_min,
        "pvp_max": pvp_max,
        "bc3_product_type": bc3_product_type,
        "bc3_has_descripcion_corta": bc3_has_descripcion_corta,
    }.items():
        if value is not None:
            filters[key] = value
    try:
        response = service.buscar_productos_paginado(
            PaginationRequestDTO(page=page, per_page=per_page, sort=sort), filters
        )
        return ProductoResponseSerializer.serialize_paginated_response(response)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda paginada: {exc}") from None


@router.get("/v2/list")
async def buscar_productos_list_v2(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: ProductoService = Depends(get_producto_service),
) -> list:
    """Legacy V2 list alias."""
    response = service.buscar_productos_paginado(
        PaginationRequestDTO(page=page, per_page=limit, sort=None), {}
    )
    return ProductoResponseSerializer.serialize_paginated_response(response)["items"]


@router.get("/")
async def get_productos(
    limit: int = Query(50, ge=1, le=500),
    service: ProductoService = Depends(get_producto_service),
) -> list:
    """Legacy V1 list response."""
    return [item.model_dump() for item in service.get_all_productos()[:limit]]


@admin_router.post(
    "/productos",
    status_code=201,
    dependencies=[Depends(verify_admin_api_key), Depends(require_admin_api_key)],
)
async def create_admin_producto(
    payload: dict, service: ProductoService = Depends(get_producto_service)
) -> dict:
    """Create a catalog product through the protected admin contract."""
    payload.setdefault("marca", "Disano")
    from app.application.dto.producto import ProductoCreateDTO

    try:
        return service.crear_producto(ProductoCreateDTO.model_validate(payload)).model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Error creando producto") from exc


@admin_router.delete("/productos/{codigo}", dependencies=[Depends(require_admin_api_key)])
async def delete_admin_producto(
    codigo: str, service: ProductoService = Depends(get_producto_service)
) -> dict:
    """Delete a catalog product through the protected admin contract."""
    if not service.eliminar_producto(codigo):
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"status": "deleted", "codigo": codigo}


@router.get("/{codigo}")
async def get_producto(
    codigo: str,
    service: ProductoService = Depends(get_producto_service),
) -> dict:
    """Legacy V1 product detail response."""
    try:
        return service.obtener_producto(codigo).model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
