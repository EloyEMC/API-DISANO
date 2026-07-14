"""Pagination Response DTOs for advanced features."""

from pydantic import BaseModel, Field


class PaginationMetadata(BaseModel):
    ."""Metadata for pagination responses."""

    total_items: int = Field(..., description="Total items matching query")
    total_pages: int = Field(..., description="Total pages")
    current_page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")

    @classmethod
    def from_query(cls, total_items: int, current_page: int, per_page: int) -> "PaginationMetadata":
        """Create metadata from query results."""
        total_pages = (total_items + per_page - 1) // per_page
        return cls(
            total_items=total_items,
            total_pages=total_pages,
            current_page=current_page,
            per_page=per_page,
            has_next=current_page < total_pages,
            has_previous=current_page > 1,
        )


class PaginatedResponseDTO(BaseModel):
    ."""Complete response DTO for paginated results."""

    items: list = Field(..., description="List of items for current page")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")
    filters_applied: dict | None = Field(None, description="Filters that were applied")
    sorting_applied: dict | None = Field(None, description="Sorting that was applied")
