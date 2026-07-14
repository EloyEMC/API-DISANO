"""Filter Criteria DTO for advanced features."""

from pydantic import BaseModel, Field, model_validator


class FilterCriteria(BaseModel):
    ."""DTO for advanced filtering with comprehensive filters."""

    marca: str | None = Field(None, max_length=50, description="Filter by brand")
    familia: str | None = Field(None, max_length=50, description="Filter by family")
    pvp_min: float | None = Field(None, ge=0, description="Min price")
    pvp_max: float | None = Field(None, ge=0, description="Max price")
    bc3_product_type: str | None = Field(None, description="BC3 product type filter")
    bc3_has_descripcion_corta: bool | None = Field(None, description="Has short description")
    buscar: str | None = Field(None, min_length=1, description="Search term")

    @model_validator(mode="after")
    def validate_price_range(self) -> "FilterCriteria":
        """Validate pvp_min <= pvp_max."""
        if self.pvp_min is not None and self.pvp_max is not None:
            if self.pvp_min > self.pvp_max:
                raise ValueError("pvp_min cannot be greater than pvp_max")
        return self
