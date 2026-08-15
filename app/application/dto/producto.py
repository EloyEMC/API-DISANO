"""Application DTOs module.

Data Transfer Objects for input/output validation in application layer.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from app.domain.entities.producto import ProductoEntity


class ProductoSearchDTOV1(BaseModel):
    """DTO for V1 search with larger limit for backward compatibility."""

    buscar: Optional[str] = Field(None, min_length=1, description="Search term")
    limit: int = Field(10, ge=1, le=500, description="Max results")
    marca: Optional[str] = Field(None, max_length=50, description="Filter by brand")
    familia: Optional[str] = Field(None, max_length=50, description="Filter by family")


# ============================================
# INPUT DTOs (Create/Update operations)
# ============================================


class ProductoCreateDTO(BaseModel):
    """DTO for creating a new product."""

    codigo: str = Field(..., min_length=1, max_length=50)
    descripcion: str = Field(..., min_length=2)
    marca: str = Field(..., min_length=1)
    familia: Optional[str] = Field(None)
    pvp: Optional[float] = Field(None, ge=0)
    bc3_descripcion_corta: Optional[str] = Field(None)
    bc3_product_type: Optional[str] = Field(None)
    bc3_descripcion_completa: Optional[str] = Field(None)

    def to_entity(self) -> ProductoEntity:
        """Convert DTO to Domain Entity."""
        return ProductoEntity(
            codigo=self.codigo,
            descripcion=self.descripcion,
            marca=self.marca,
            familia=self.familia,
            pvp=self.pvp,
            bc3_descripcion_corta=self.bc3_descripcion_corta,
            bc3_product_type=self.bc3_product_type,
            bc3_descripcion_completa=self.bc3_descripcion_completa,
            created_at=None,
            updated_at=None,
        )


class ProductoUpdateDTO(BaseModel):
    """DTO for updating an existing product."""

    descripcion: Optional[str] = Field(None, min_length=2)
    marca: Optional[str] = Field(None, min_length=1)
    familia: Optional[str] = Field(None)
    pvp: Optional[float] = Field(None, ge=0)
    bc3_descripcion_corta: Optional[str] = Field(None)
    bc3_product_type: Optional[str] = Field(None)
    bc3_descripcion_completa: Optional[str] = Field(None)


class ProductoSearchDTO(BaseModel):
    """DTO for searching products with filters."""

    buscar: Optional[str] = Field(None, min_length=1)
    limit: int = Field(10, ge=1, le=100)
    marca: Optional[str] = Field(None, max_length=50)
    familia: Optional[str] = Field(None, max_length=50)


class ProductoPrecioUpdateDTO(BaseModel):
    """DTO for updating product price only."""

    pvp: float = Field(..., ge=0)


# ============================================
# OUTPUT DTOs (Response formatting)
# ============================================


class ProductoExternalResponse(BaseModel):
    """Stable public product contract (discounts and logistics excluded)."""

    model_config = {"extra": "ignore"}

    codigo: str
    descripcion: str
    marca: str
    familia: Optional[str] = None
    pvp: Optional[float] = None
    descripcion_corta: Optional[str] = None
    familia_web: Optional[str] = None
    serie_familia_1: Optional[str] = None
    familia_catalogo: Optional[str] = None
    familia_catalogo_ptl: Optional[str] = None
    url_ficha_tec: Optional[str] = None
    codigo_web: Optional[str] = None
    referencia: Optional[str] = None
    ean_13: Optional[str] = None
    imagen: Optional[str] = None
    img_url: Optional[str] = None
    descontinuado: Optional[int] = None
    bc3_descripcion_corta: Optional[str] = None
    bc3_descripcion_completa: Optional[str] = None
    bc3_descripcion_larga: Optional[str] = None
    bc3_product_type: Optional[str] = None
    raee_a: Optional[float] = None
    raee_l: Optional[float] = None
    raee_t: Optional[float] = None
    bc3_processed_at: Optional[datetime] = None


class ProductoExternalPage(BaseModel):
    """Versioned public paginated response."""

    items: list[ProductoExternalResponse]
    pagination: dict
    filters_applied: dict | None = None
    sorting_applied: dict | None = None


class ProductoResponseDTO(BaseModel):
    """DTO for product responses."""

    codigo: str
    descripcion: str
    marca: str
    familia: Optional[str] = None
    pvp: Optional[float] = None
    bc3_descripcion_corta: Optional[str] = None
    bc3_product_type: Optional[str] = None
    bc3_descripcion_completa: Optional[str] = None

    @classmethod
    def from_entity(cls, entity: ProductoEntity) -> "ProductoResponseDTO":
        """Create response DTO from Domain Entity."""
        return cls(
            codigo=entity.codigo,
            descripcion=entity.descripcion,
            marca=entity.marca,
            familia=entity.familia,
            pvp=entity.pvp,
            bc3_descripcion_corta=entity.bc3_descripcion_corta,
            bc3_product_type=entity.bc3_product_type,
            bc3_descripcion_completa=entity.bc3_descripcion_completa,
        )


class ProductoListResponseDTO(BaseModel):
    """DTO for list of products response."""

    productos: list[ProductoResponseDTO]
    total: int
    limit: int
    filtered: bool

    @classmethod
    def from_entities(
        cls, entities: list[ProductoEntity], limit: int, has_filters: bool
    ) -> "ProductoListResponseDTO":
        """Create list response from Domain Entities."""
        return cls(
            productos=[ProductoResponseDTO.from_entity(e) for e in entities],
            total=len(entities),
            limit=limit,
            filtered=has_filters,
        )
