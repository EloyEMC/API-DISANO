"""Test package import for pagination DTOs."""


def test_pagination_dto_package_import() -> None:
    ."""Test that pagination DTO package can be imported."""
    from app.application.dto.pagination import (
        PaginationRequestDTO,
        PaginatedResponseDTO,
        PaginationMetadata,
        SortCriteria,
        FilterCriteria,
        V1ToV2Adapter,
    )

    # Verify all DTOs are importable
    assert PaginationRequestDTO is not None
    assert PaginatedResponseDTO is not None
    assert PaginationMetadata is not None
    assert SortCriteria is not None
    assert FilterCriteria is not None
    assert V1ToV2Adapter is not None
