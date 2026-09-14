"""Strict DTOs and canonical hashing for NEW catalog imports."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.application.services.github_approval import GitHubApprovalReference


class CatalogProductRow(BaseModel):
    """Canonical workbook product row restricted to new products."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)
    web_code: str | None = None
    reference: str | None = None
    ean: str | None = None
    description: str = Field(..., min_length=2)
    pvp: float | None = Field(None, ge=0)
    dto: str | None = None
    up_log: float | None = None
    u_caja: int | None = None
    estado: Literal["NEW"]
    etim: str | None = None
    raee: float | None = None
    raee_l: float | None = None
    raee_t: float | None = None
    dimensions: dict[str, float | None] = Field(default_factory=dict)
    weights: dict[str, float | None] = Field(default_factory=dict)
    volumes: dict[str, float | None] = Field(default_factory=dict)
    family: dict[str, str | None] = Field(default_factory=dict)
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

    @field_validator("code", "brand", mode="before")
    @classmethod
    def strip_required(cls, value: str) -> str:
        """Strip required catalog text fields."""
        return value.strip()


class CatalogImportRequest(BaseModel):
    """Validated request for an approval-bound catalog import."""

    model_config = ConfigDict(extra="forbid")

    source_snapshot_id: str = Field(..., min_length=1, max_length=255)
    source_hash: str = Field(..., min_length=64, max_length=64)
    github_pr: GitHubApprovalReference
    rows: list[CatalogProductRow] = Field(..., min_length=1)

    @field_validator("source_hash")
    @classmethod
    def validate_hash(cls, value: str) -> str:
        """Normalize and validate the source snapshot hash."""
        value = value.lower().strip()
        if any(c not in "0123456789abcdef" for c in value):
            raise ValueError("source_hash must be hexadecimal")
        return value


def canonical_catalog_payload(rows: list[CatalogProductRow]) -> str:
    """Serialize catalog rows into their canonical JSON payload."""
    bc3_fields = {
        "bc3_descripcion_corta",
        "bc3_descripcion_larga",
        "bc3_descripcion_completa",
        "bc3_product_type",
        "bc3_descripcion_corta_ca",
        "bc3_descripcion_larga_ca",
        "bc3_descripcion_corta_gl",
        "bc3_descripcion_larga_gl",
    }
    payload = []
    for row in rows:
        values = row.model_dump(mode="json", exclude_none=False)
        payload.append(
            {
                key: value
                for key, value in values.items()
                if key not in bc3_fields or value is not None
            }
        )
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def catalog_payload_hash(rows: list[CatalogProductRow]) -> str:
    """Compute the SHA-256 hash of the canonical catalog payload."""
    return hashlib.sha256(canonical_catalog_payload(rows).encode("utf-8")).hexdigest()


def _ean_to_raw_value(ean: str | None) -> int | None:
    """Serialize the text EAN contract to a PostgreSQL-compatible integer."""
    if ean is None or not ean.strip():
        return None

    try:
        numeric_ean = Decimal(ean.strip())
    except (InvalidOperation, ValueError):
        raise ValueError("EAN must be a whole number") from None

    if not numeric_ean.is_finite() or numeric_ean != numeric_ean.to_integral_value():
        raise ValueError("EAN must be a whole number")
    return int(numeric_ean)


def row_to_raw_values(row: CatalogProductRow) -> dict[str, Any]:
    """Map every canonical NEW-row field to the raw-product ORM attribute."""
    values: dict[str, Any] = {
        "codigo": row.code,
        "marca": row.brand,
        "codigo_web": row.web_code,
        "referencia": row.reference,
        "ean_13": _ean_to_raw_value(row.ean),
        "descripcion": row.description,
        "dto": row.dto,
        "pvp": row.pvp,
        "up_log": row.up_log,
        "u_caja": row.u_caja,
        "clase_etim": row.etim,
        "raee_a": row.raee,
        "raee_l": row.raee_l,
        "raee_t": row.raee_t,
        "imagen": row.imagen,
        "img_url": row.img_url,
        "url_ficha_tec": row.url_ficha_tec,
        "bc3_descripcion_corta": row.bc3_descripcion_corta,
        "bc3_descripcion_larga": row.bc3_descripcion_larga,
        "bc3_descripcion_completa": row.bc3_descripcion_completa,
        "bc3_product_type": row.bc3_product_type,
        "bc3_descripcion_corta_ca": row.bc3_descripcion_corta_ca,
        "bc3_descripcion_larga_ca": row.bc3_descripcion_larga_ca,
        "bc3_descripcion_corta_gl": row.bc3_descripcion_corta_gl,
        "bc3_descripcion_larga_gl": row.bc3_descripcion_larga_gl,
    }
    # Keep both historical names synchronized at the persistence boundary.
    # Older producers call the long BC3 description ``completa`` while the
    # public API contract calls it ``larga``.
    if values["bc3_descripcion_larga"] is None:
        values["bc3_descripcion_larga"] = values["bc3_descripcion_completa"]
    if values["bc3_descripcion_completa"] is None:
        values["bc3_descripcion_completa"] = values["bc3_descripcion_larga"]
    aliases = {
        "length_m": "longitud_m",
        "length_mm": "longitud_mm",
        "width_m": "ancho_m",
        "width_mm": "ancho_mm",
        "height_m": "alto_m",
        "height_mm": "altura_mm",
        "volume_dm3": "volumen_dm3",
        "dm3": "volumen_dm3",
        "volume_cm3": "cm3",
        "gross_kg": "peso_bruto_kg",
        "gross_g": "peso_bruto_gr",
        "net_kg": "peso_neto_kg",
        "net_g": "peso_neto_gr",
        "web": "familia_web",
        "catalog": "familia_catalogo",
        "catalog_ptl": "familia_catalogo_ptl",
    }
    for group in (row.dimensions, row.weights, row.volumes, row.family):
        for key, value in group.items():
            values[aliases.get(key, key)] = value
    return values
