"""HTTP routes for the insert-only NEW catalog import workflow."""

from fastapi import APIRouter, Depends, Header, HTTPException

from app.application.dto.catalog_import import CatalogImportRequest
from app.application.services.catalog_import import CatalogImportService
from app.application.services.github_approval import (
    GitHubApprovalUnavailable,
    GitHubApprovalVerifier,
)
from app.config import get_settings
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository
from app.interfaces.http.productos import verify_bc3_api_key

router = APIRouter(prefix="/productos/bc3/v1/catalog-import", tags=["catalog-import"])


def get_service() -> CatalogImportService:
    """Construct the catalog import service and verifier."""
    settings = get_settings()
    verifier = GitHubApprovalVerifier(
        token=getattr(settings, "github_api_token", None),
        expected_repository=getattr(settings, "github_expected_repository", None),
        api_base_url=getattr(settings, "github_api_url", "https://api.github.com"),
        required_approvals=getattr(settings, "github_required_approvals", 1),
        approval_mode=getattr(settings, "bc3_approval_mode", "github_review"),
    )
    session = SessionLocal()
    return CatalogImportService(SQLAlchemyProductoRepository(session), verifier)


@router.post("/preview", dependencies=[Depends(verify_bc3_api_key)])
def preview(
    request: CatalogImportRequest,
    actor_id: str = Header(..., alias="X-BC3-Actor"),
    service: CatalogImportService = Depends(get_service),
) -> dict:
    """Create a catalog import preview."""
    return service.preview(request, actor_id)


@router.post("/approve", dependencies=[Depends(verify_bc3_api_key)])
def approve(
    snapshot_id: str,
    request: CatalogImportRequest,
    actor_id: str = Header(..., alias="X-BC3-Actor"),
    approval_key: str | None = Header(None, alias="X-BC3-Approval-Key"),
    service: CatalogImportService = Depends(get_service),
) -> dict:
    """Approve a catalog import snapshot with the dedicated credential."""
    settings = get_settings()
    if approval_key not in settings.bc3_approval_keys_list:
        raise HTTPException(
            status_code=403, detail="Dedicated catalog approval credential required"
        )
    try:
        return service.approve(snapshot_id, actor_id, request)
    except GitHubApprovalUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.post("/apply", dependencies=[Depends(verify_bc3_api_key)])
def apply(
    snapshot_id: str,
    request: CatalogImportRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    actor_id: str = Header(..., alias="X-BC3-Actor"),
    approval_key: str | None = Header(None, alias="X-BC3-Approval-Key"),
    service: CatalogImportService = Depends(get_service),
) -> dict:
    """Apply an approved catalog import snapshot."""
    settings = get_settings()
    if approval_key not in settings.bc3_approval_keys_list:
        raise HTTPException(
            status_code=403, detail="Dedicated catalog approval credential required"
        )
    try:
        return service.apply(snapshot_id, actor_id, request, idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
