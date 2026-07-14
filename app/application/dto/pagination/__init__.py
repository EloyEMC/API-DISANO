"""Pagination DTOs package for advanced features.

This package contains DTOs for pagination, sorting, and filtering functionality.
."""

from pydantic import BaseModel

from app.application.dto.pagination.pagination_request import PaginationRequestDTO
from app.application.dto.pagination.pagination_response import (
    PaginatedResponseDTO,
    PaginationMetadata,
)
from app.application.dto.pagination.sort_criteria import SortCriteria
from app.application.dto.pagination.filter_criteria import FilterCriteria


# Placeholder classes - will be implemented in subsequent tasks
class V1ToV2Adapter:
    """Adapter for V1 to V2 compatibility."""

    pass


# Export all DTOs
__all__ = [
    "PaginationRequestDTO",
    "PaginatedResponseDTO",
    "PaginationMetadata",
    "SortCriteria",
    "FilterCriteria",
    "V1ToV2Adapter",
]
