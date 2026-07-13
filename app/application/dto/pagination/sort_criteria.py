"""Sort Criteria DTO for advanced features."""

from pydantic import BaseModel, Field, field_validator


class SortCriteria(BaseModel):
    """DTO for sorting criteria with field validation."""

    field: str = Field(..., description="Field to sort by")
    order: str = Field("asc", description="Sort order (asc or desc)")

    @field_validator("order")
    @classmethod
    def normalize_order(cls, v: str) -> str:
        """Normalize order to lowercase."""
        return v.lower()

    @field_validator("field")
    @classmethod
    def validate_field(cls, v: str) -> str:
        """Validate field against whitelist."""
        allowed_fields = [
            "codigo",
            "descripcion",
            "marca",
            "familia",
            "pvp",
            "bc3_descripcion_corta",
            "bc3_product_type",
        ]
        if v not in allowed_fields:
            raise ValueError(f"Sort field must be one of: {allowed_fields}")
        return v
