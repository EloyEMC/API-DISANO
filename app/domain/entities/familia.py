"""Domain entity for Familia

Represents a product family with BC3 statistics - independent of database
or HTTP concerns. This is a domain-level aggregation entity.
."""

from pydantic import BaseModel, Field, field_validator


class FamiliaEntity(BaseModel):
    """Domain entity representing a Product Family with BC3 statistics

    This entity represents an aggregation of product data by family,
    including BC3 coverage statistics. It's a read-only aggregation
    used for reporting and statistics.

    Attributes:
        nombre: Family name (e.g., "Emergencia", "Interiores")
        total_productos: Total number of products in this family
        con_bc3: Number of products with BC3 descriptions
        con_imagen: Number of products with images
        descontinuados: Number of discontinued products
    """

    # Core identity fields
    nombre: str = Field(..., min_length=1, description="Family name")

    # Statistics fields
    total_productos: int = Field(..., ge=0, description="Total products in family")
    con_bc3: int = Field(..., ge=0, description="Products with BC3 data")
    con_imagen: int = Field(..., ge=0, description="Products with images")
    descontinuados: int = Field(..., ge=0, description="Discontinued products")

    @field_validator("total_productos")
    @classmethod
    def validate_counts_consistency(cls, value, info):
        """Validate that counts don't exceed total."""
        if info.data:
            con_bc3 = info.data.get("con_bc3", 0)
            con_imagen = info.data.get("con_imagen", 0)
            descontinuados = info.data.get("descontinuados", 0)

            if value < max(con_bc3, con_imagen, descontinuados):
                raise ValueError(
                    f"total_productos ({value}) cannot be less than individual counts: "
                    f"con_bc3={con_bc3}, con_imagen={con_imagen}, descontinuados={descontinuados}"
                )
        return value

    def get_bc3_coverage_percentage(self) -> float:
        """Calculate BC3 coverage as percentage."""
        if self.total_productos == 0:
            return 0.0
        return (self.con_bc3 / self.total_productos) * 100

    def get_imagen_coverage_percentage(self) -> float:
        """Calculate image coverage as percentage."""
        if self.total_productos == 0:
            return 0.0
        return (self.con_imagen / self.total_productos) * 100

    class Config:
        """Pydantic configuration."""

        # Immutable entity
        frozen = True

        # Validate assignment
        validate_assignment = True
