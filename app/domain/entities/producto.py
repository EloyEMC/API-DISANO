"""Domain entity for Producto.

Represents a product in the domain layer - independent of database
or HTTP concerns. This is the core business object.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class ProductoEntity(BaseModel):
    """Domain entity representing a Product.

    This entity is immutable (frozen=True) to ensure domain rules
    are enforced at creation time.

    Attributes:
        codigo: Unique product identifier
        descripcion: Full product description
        marca: Product brand/manufacturer
        familia: Product family/category
        pvp: Public sales price (optional)
        bc3_descripcion_corta: BC3 Suite short description
        bc3_product_type: BC3 Suite product type
        bc3_descripcion_completa: BC3 Suite full description
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    # Core identity fields
    codigo: str = Field(..., min_length=1, description="Unique product code")
    descripcion: str = Field(..., min_length=2, description="Product description")
    marca: str = Field(..., min_length=1, description="Product brand")

    # Optional fields
    familia: Optional[str] = Field(None, description="Product family")
    pvp: Optional[float] = Field(None, ge=0, description="Public sales price")
    descripcion_corta: Optional[str] = None
    familia_web: Optional[str] = None
    serie_familia_1: Optional[str] = None
    familia_catalogo: Optional[str] = None
    familia_catalogo_ptl: Optional[str] = None
    url_ficha_tec: Optional[str] = None

    # BC3 Suite integration fields
    bc3_descripcion_corta: Optional[str] = Field(None, description="BC3 Suite short description")
    bc3_product_type: Optional[str] = Field(None, description="BC3 Suite product type")
    bc3_descripcion_completa: Optional[str] = Field(None, description="BC3 Suite full description")
    bc3_descripcion_larga: Optional[str] = Field(None, description="BC3 Suite long description")

    # Additional fields (from productos table)
    codigo_web: Optional[str] = Field(None, description="Web code")
    referencia: Optional[str] = Field(None, description="Reference")
    ean_13: Optional[str] = Field(None, description="EAN-13 barcode")
    imagen: Optional[str] = Field(None, description="Image filename")
    img_url: Optional[str] = Field(None, description="Image URL")
    descontinuado: Optional[int] = Field(None, description="Discontinued flag")

    # Private BC3 contract fields; never expose these in the public contract.
    dto: Optional[str] = None
    up_log: Optional[float] = None
    u_caja: Optional[int] = None
    clase_etim: Optional[str] = None
    peso_bruto_kg: Optional[float] = None
    peso_bruto_gr: Optional[float] = None
    peso_neto_kg: Optional[float] = None
    peso_neto_gr: Optional[float] = None
    longitud_m: Optional[float] = None
    longitud_mm: Optional[float] = None
    ancho_m: Optional[float] = None
    ancho_mm: Optional[float] = None
    alto_m: Optional[float] = None
    altura_mm: Optional[float] = None
    volumen_dm3: Optional[float] = None
    cm3: Optional[float] = None

    # Energy efficiency / recycling fields (RAEE)
    raee_a: Optional[float] = Field(
        None, description="RAEE aparatos (electrical appliances recycling fee)"
    )
    raee_l: Optional[float] = Field(None, description="RAEE lámparas (lamps recycling fee)")
    raee_t: Optional[float] = Field(None, description="RAEE total (aparatos + lámparas)")

    # Audit fields
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @field_validator("pvp", mode="before")
    @classmethod
    def validate_pvp(cls, value: float | None) -> float | None:
        """Validate that price is non-negative."""
        if value is not None and value < 0:
            raise ValueError("Price cannot be negative")
        return value

    class Config:
        """Pydantic configuration."""

        # Immutable entity - prevents modification after creation
        frozen = True

        # Use enum values instead of names
        use_enum_values = True

        # Validate assignment (redundant with frozen but explicit)
        validate_assignment = True
