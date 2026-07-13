"""Pagination Request DTO for advanced features."""

from pydantic import BaseModel, Field


class PaginationRequestDTO(BaseModel):
    """DTO for pagination requests with comprehensive validation."""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    sort: str | None = Field(None, description="Sort criteria (e.g., 'precio:desc')")

    @property
    def offset(self) -> int:
        """Calculate offset from page and per_page."""
        return (self.page - 1) * self.per_page
