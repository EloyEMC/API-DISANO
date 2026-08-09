"""Private BC3 enrichment contracts."""

import hashlib
import json

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


BC3_ENRICHMENT_FIELDS: tuple[str, ...] = (
    "bc3_descripcion_corta",
    "bc3_descripcion_larga",
    "bc3_descripcion_completa",
    "bc3_product_type",
)
MAX_BC3_ENRICHMENT_BATCH_SIZE = 100


class BC3EnrichmentItem(BaseModel):
    """One proposed BC3 enrichment."""

    model_config = ConfigDict(extra="forbid")

    codigo: str = Field(..., min_length=1, max_length=100)
    bc3_descripcion_corta: str | None = None
    bc3_descripcion_larga: str | None = None
    bc3_descripcion_completa: str | None = None
    bc3_product_type: str | None = None

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

    @model_validator(mode="after")
    def reject_duplicate_codes(self) -> "BC3EnrichmentPreviewRequest":
        """Reject duplicate codes after canonical normalization."""
        codes = [item.codigo for item in self.items]
        if len(codes) != len(set(codes)):
            raise ValueError("items must not contain duplicate codigo values")
        return self


class BC3EnrichmentApplyRequest(BC3EnrichmentPreviewRequest):
    """Bounded batch of BC3 enrichment values to persist atomically."""


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
    """Read-only BC3 enrichment preview response."""

    model_config = ConfigDict(extra="forbid")

    items: list[BC3EnrichmentPreviewItem]
    missing_codes: list[str]


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
    created_at: object
    completed_at: object | None = None
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
        {field: item.get(field) for field in ("codigo", *BC3_ENRICHMENT_FIELDS)} for item in items
    ]
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def hash_bc3_enrichment_items(items: list[dict]) -> str:
    """Hash only the canonical request representation; never log its contents."""
    return hashlib.sha256(canonicalize_bc3_enrichment_items(items).encode("utf-8")).hexdigest()
