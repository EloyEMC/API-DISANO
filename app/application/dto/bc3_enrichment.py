"""Private BC3 enrichment contracts."""

import hashlib
import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.application.services.github_approval import GitHubApprovalReference

BC3_ENRICHMENT_FIELDS: tuple[str, ...] = (
    "imagen",
    "img_url",
    "url_ficha_tec",
    "bc3_descripcion_corta",
    "bc3_descripcion_larga",
    "bc3_descripcion_completa",
    "bc3_product_type",
    "bc3_descripcion_corta_ca",
    "bc3_descripcion_larga_ca",
    "bc3_descripcion_corta_gl",
    "bc3_descripcion_larga_gl",
)
MAX_BC3_ENRICHMENT_BATCH_SIZE = 100


class BC3EnrichmentItem(BaseModel):
    """One proposed BC3 enrichment."""

    model_config = ConfigDict(extra="forbid")

    codigo: str = Field(..., min_length=1, max_length=100)
    imagen: str | None = None
    img_url: str | None = None
    url_ficha_tec: str | None = None
    bc3_descripcion_corta: str | None = None
    bc3_descripcion_larga: str | None = None
    bc3_descripcion_completa: str | None = None
    bc3_product_type: str | None = None
    bc3_descripcion_corta_ca: str | None = None
    bc3_descripcion_larga_ca: str | None = None
    bc3_descripcion_corta_gl: str | None = None
    bc3_descripcion_larga_gl: str | None = None

    @field_validator("codigo")
    @classmethod
    def normalize_codigo(cls, value: str) -> str:
        """Require the canonical product-code representation."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("codigo must not be blank")
        return normalized


class BC3EnrichmentPreviewRequest(BaseModel):
    """Bounded batch of BC3 enrichment proposals."""

    model_config = ConfigDict(extra="forbid")

    items: list[BC3EnrichmentItem] = Field(
        ..., min_length=1, max_length=MAX_BC3_ENRICHMENT_BATCH_SIZE
    )
    github_pr: GitHubApprovalReference

    @model_validator(mode="after")
    def reject_duplicate_codes(self) -> "BC3EnrichmentPreviewRequest":
        """Reject duplicate codes after canonical normalization."""
        codes = [item.codigo for item in self.items]
        if len(codes) != len(set(codes)):
            raise ValueError("items must not contain duplicate codigo values")
        return self


class BC3EnrichmentApplyRequest(BC3EnrichmentPreviewRequest):
    """Apply only a previously approved, immutable preview snapshot."""

    preview_id: str = Field(..., min_length=1, max_length=100)


class BC3EnrichmentApprovalRequest(BaseModel):
    """Explicit approval of a durable preview snapshot."""

    model_config = ConfigDict(extra="forbid")

    preview_id: str = Field(..., min_length=1, max_length=100)
    github_pr: GitHubApprovalReference


class BC3EnrichmentApprovalResponse(BaseModel):
    """Safe acknowledgement containing the exact approval reference."""

    model_config = ConfigDict(extra="forbid")

    preview_id: str
    status: str
    github_pr: GitHubApprovalReference | None = None
    github_approval_count: int | None = None
    github_approval_mode: str = "github_review"


class BC3EnrichmentChange(BaseModel):
    """One field difference proposed by the preview."""

    model_config = ConfigDict(extra="forbid")

    field: str
    current_value: str | None = None
    proposed_value: str | None = None


class BC3EnrichmentPreviewItem(BaseModel):
    """Preview result for an existing product code."""

    model_config = ConfigDict(extra="forbid")

    codigo: str
    changes: list[BC3EnrichmentChange]


class BC3EnrichmentPreviewResponse(BaseModel):
    """Durable preview response; values are intentionally not exposed by status."""

    model_config = ConfigDict(extra="forbid")

    preview_id: str
    status: str
    expires_at: datetime
    request_hash: str
    items: list[BC3EnrichmentPreviewItem]
    missing_codes: list[str]
    github_pr: GitHubApprovalReference
    github_approval_status: str = "pending"
    github_approval_count: int | None = None
    github_approval_mode: str = "github_review"


class BC3EnrichmentJobItemStatus(BaseModel):
    """Safe per-item result for a durable enrichment job."""

    model_config = ConfigDict(extra="forbid")

    codigo: str
    result_status: str
    error_message: str | None = None


class BC3EnrichmentJobStatusResponse(BaseModel):
    """Safe durable status and audit projection for an enrichment job."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: str
    total_items: int
    updated_items: int
    unchanged_items: int
    missing_items: int
    created_at: datetime
    completed_at: datetime | None = None
    items: list[BC3EnrichmentJobItemStatus]


class BC3EnrichmentApplyResponse(BaseModel):
    """Result of a transactional BC3 enrichment apply."""

    model_config = ConfigDict(extra="forbid")

    updated_codes: list[str]
    unchanged_codes: list[str]
    job_id: str
    status: str
    missing_codes: list[str] = Field(default_factory=list)


def canonicalize_bc3_enrichment_items(items: list[dict]) -> str:
    """Return a deterministic representation of normalized enrichment items."""
    normalized = [
        {
            "codigo": item["codigo"],
            **{field: item[field] for field in BC3_ENRICHMENT_FIELDS if field in item},
        }
        for item in items
    ]
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def hash_bc3_enrichment_items(items: list[dict]) -> str:
    """Hash only the canonical request representation; never log its contents."""
    return hashlib.sha256(canonicalize_bc3_enrichment_items(items).encode("utf-8")).hexdigest()
