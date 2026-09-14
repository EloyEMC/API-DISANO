from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from app.application.dto.bc3_enrichment import (
    BC3EnrichmentApplyRequest,
    BC3EnrichmentItem,
    BC3EnrichmentPreviewRequest,
)
from app.application.services.github_approval import (
    GitHubApprovalEvidence,
    GitHubApprovalReference,
    GitHubApprovalVerifier,
)
from app.config import Settings
from app.domain.entities.producto import ProductoEntity
from app.domain.repositories.producto import ProductoRepositoryInterface
from app.domain.services.producto import ProductoService

ItemPayload = dict[str, object]


class ApprovalFakeRepository(ProductoRepositoryInterface):
    def __init__(self) -> None:
        self.products: dict[str, ProductoEntity] = {
            "P-1": ProductoEntity(
                codigo="P-1",
                descripcion="Product",
                marca="Brand",
                familia=None,
                pvp=None,
                bc3_product_type=None,
                bc3_descripcion_completa=None,
                bc3_descripcion_larga=None,
                codigo_web=None,
                referencia=None,
                ean_13=None,
                imagen=None,
                img_url=None,
                descontinuado=None,
                raee_a=None,
                raee_l=None,
                raee_t=None,
                created_at=None,
                updated_at=None,
                bc3_descripcion_corta="old",
            )
        }
        self.previews: dict[str, dict[str, object]] = {}
        self.jobs: dict[str, dict[str, object]] = {}
        self.next_id = 1

    def get_by_codigo(self, codigo: str) -> ProductoEntity:
        return self.products[codigo]

    def buscar_productos(
        self, termino: str = "", limit: int = 10, marca: str = "", familia: str = ""
    ) -> list[ProductoEntity]:
        del termino, limit, marca, familia
        return list(self.products.values())

    def get_all(self, skip: int = 0, limit: int = 100) -> list[ProductoEntity]:
        return list(self.products.values())[skip : skip + limit]

    def save(self, producto: ProductoEntity) -> ProductoEntity:
        self.products[producto.codigo] = producto
        return producto

    def delete(self, codigo: str) -> bool:
        return self.products.pop(codigo, None) is not None

    def count_total(self) -> int:
        return len(self.products)

    def buscar_productos_paginado(self, dto: dict[str, Any]) -> tuple[list[ProductoEntity], int]:
        del dto
        products = list(self.products.values())
        return products, len(products)

    def get_private_by_codigos(self, codes: list[str]) -> dict[str, ProductoEntity]:
        return {code: self.products[code] for code in codes if code in self.products}

    def create_bc3_preview(
        self,
        items: list[ItemPayload],
        actor_id: str,
        source_snapshot_id: str,
        github_pr: GitHubApprovalReference,
    ) -> dict[str, object]:
        preview_id = f"preview-{self.next_id}"
        self.next_id += 1
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        self.previews[preview_id] = {
            "items": items,
            "actor_id": actor_id,
            "status": "pending",
            "expires_at": expires_at,
            "github_pr": github_pr,
            "source_snapshot_id": source_snapshot_id,
        }
        return {
            "preview_id": preview_id,
            "request_hash": "hash",
            "expires_at": expires_at,
        }

    def approve_bc3_preview(
        self,
        preview_id: str,
        actor_id: str,
        scope: str,
        github_pr: GitHubApprovalReference,
        evidence: GitHubApprovalEvidence,
    ) -> None:
        del scope
        preview = self.previews[preview_id]
        if (
            preview["status"] != "pending"
            or preview["actor_id"] != actor_id
            or preview["github_pr"] != github_pr
        ):
            raise ValueError("preview is not eligible for approval")
        preview["status"] = "approved"
        preview["evidence"] = evidence

    def apply_bc3_enrichment(
        self,
        items: list[ItemPayload],
        key: str,
        preview_id: str,
        actor_id: str,
        github_pr: GitHubApprovalReference,
    ) -> dict[str, object]:
        for job in self.jobs.values():
            if job["key"] == key:
                if job["items"] != items:
                    raise ValueError(
                        "idempotency key has already been used with a different request"
                    )
                return job["result"]  # type: ignore[return-value]
        preview = self.previews[preview_id]
        if (
            preview["status"] != "approved"
            or preview["actor_id"] != actor_id
            or preview["github_pr"] != github_pr
        ):
            raise ValueError(
                "approved preview is invalid, expired, used, or does not match payload"
            )
        updated: list[str] = []
        unchanged: list[str] = []
        for item in items:
            codigo = item["codigo"]
            if not isinstance(codigo, str):
                raise TypeError("codigo must be a string")
            product = self.products[codigo]
            value = item.get("bc3_descripcion_corta")
            if product.bc3_descripcion_corta == value:
                unchanged.append(codigo)
            else:
                self.products[codigo] = product.model_copy(update={"bc3_descripcion_corta": value})
                updated.append(codigo)
        preview["status"] = "used"
        result: dict[str, object] = {
            "updated_codes": updated,
            "unchanged_codes": unchanged,
            "missing_codes": [],
            "job_id": f"job-{len(self.jobs) + 1}",
            "status": "completed",
        }
        self.jobs[str(result["job_id"])] = {
            "key": key,
            "items": items,
            "result": result,
        }
        return result


class ApprovedFakeVerifier(GitHubApprovalVerifier):
    def __init__(self) -> None:
        super().__init__(token="t" * 20, expected_repository="acme/catalog")

    def verify(self, reference: GitHubApprovalReference) -> GitHubApprovalEvidence:
        return GitHubApprovalEvidence(
            reference.repository,
            reference.pull_request_number,
            reference.head_sha,
            1,
            datetime.now(timezone.utc),
        )


def _github_pr() -> GitHubApprovalReference:
    return GitHubApprovalReference(
        repository="acme/catalog", pull_request_number=42, head_sha="a" * 40
    )


def _request(value: str = "new") -> BC3EnrichmentPreviewRequest:
    return BC3EnrichmentPreviewRequest(
        items=[BC3EnrichmentItem(codigo="P-1", bc3_descripcion_corta=value)],
        github_pr=_github_pr(),
    )


def _apply(preview_id: str, value: str = "new") -> BC3EnrichmentApplyRequest:
    return BC3EnrichmentApplyRequest(
        preview_id=preview_id,
        items=[BC3EnrichmentItem(codigo="P-1", bc3_descripcion_corta=value)],
        github_pr=_github_pr(),
    )


def test_preview_and_approval_are_bound_to_github_and_actor() -> None:
    repository = ApprovalFakeRepository()
    service = ProductoService(repository, ApprovedFakeVerifier())
    preview = service.preview_bc3_enrichment(_request(), "actor-a")
    assert preview.github_pr == _github_pr()
    service.approve_bc3_preview(preview.preview_id, "actor-a", "bc3-enrichment", _github_pr())
    with pytest.raises(ValueError, match="not eligible"):
        service.approve_bc3_preview(preview.preview_id, "actor-a", "bc3-enrichment", _github_pr())


def test_apply_requires_approved_preview_and_exact_actor() -> None:
    repository = ApprovalFakeRepository()
    service = ProductoService(repository, ApprovedFakeVerifier())
    preview = service.preview_bc3_enrichment(_request(), "actor-a")
    with pytest.raises(ValueError, match="approved preview"):
        service.apply_bc3_enrichment(_apply(preview.preview_id), "key-1", "actor-a")
    service.approve_bc3_preview(preview.preview_id, "actor-a", "bc3-enrichment", _github_pr())
    with pytest.raises(ValueError, match="approved preview"):
        service.apply_bc3_enrichment(_apply(preview.preview_id), "key-1", "actor-b")


def test_apply_replays_idempotency_and_conflicts_on_different_payload() -> None:
    repository = ApprovalFakeRepository()
    service = ProductoService(repository, ApprovedFakeVerifier())
    preview = service.preview_bc3_enrichment(_request(), "actor-a")
    service.approve_bc3_preview(preview.preview_id, "actor-a", "bc3-enrichment", _github_pr())
    first = service.apply_bc3_enrichment(_apply(preview.preview_id), "key-1", "actor-a")
    assert service.apply_bc3_enrichment(_apply(preview.preview_id), "key-1", "actor-a") == first
    with pytest.raises(ValueError, match="different request"):
        service.apply_bc3_enrichment(_apply(preview.preview_id, "other"), "key-1", "actor-a")


def test_settings_default_to_github_review_mode() -> None:
    settings = Settings()

    assert settings.bc3_approval_mode == "github_review"


def test_settings_accept_only_supported_approval_modes() -> None:
    assert Settings(bc3_approval_mode="sole_maintainer").bc3_approval_mode == "sole_maintainer"
    with pytest.raises(ValueError):
        Settings(bc3_approval_mode="disabled")


def test_settings_keep_processing_keys_separate_from_approval_keys() -> None:
    settings = Settings(api_keys="processing", bc3_api_keys="bc3", bc3_approval_keys="approval")
    assert settings.api_keys_list == ["processing"]
    assert settings.bc3_api_keys_list == ["bc3"]
    assert settings.bc3_approval_keys_list == ["approval"]
    assert settings.bc3_preview_ttl_seconds == 900
