"""Tests for PaginatedResponseDTO and PaginationMetadata."""


def test_pagination_metadata_from_query_calculation() -> None:
    ."""Test metadata calculation from query results."""
    from app.application.dto.pagination import PaginationMetadata

    metadata = PaginationMetadata.from_query(total_items=95, current_page=2, per_page=20)

    assert metadata.total_items == 95
    assert metadata.total_pages == 5
    assert metadata.current_page == 2
    assert metadata.per_page == 20
    assert metadata.has_next is True
    assert metadata.has_previous is True


def test_pagination_metadata_on_last_page() -> None:
    ."""Test metadata on last page."""
    from app.application.dto.pagination import PaginationMetadata

    metadata = PaginationMetadata.from_query(total_items=95, current_page=5, per_page=20)

    assert metadata.total_items == 95
    assert metadata.total_pages == 5
    assert metadata.current_page == 5
    assert metadata.per_page == 20
    assert metadata.has_next is False
    assert metadata.has_previous is True


def test_pagination_metadata_on_first_page() -> None:
    ."""Test metadata on first page."""
    from app.application.dto.pagination import PaginationMetadata

    metadata = PaginationMetadata.from_query(total_items=95, current_page=1, per_page=20)

    assert metadata.total_items == 95
    assert metadata.total_pages == 5
    assert metadata.current_page == 1
    assert metadata.per_page == 20
    assert metadata.has_next is True
    assert metadata.has_previous is False


def test_pagination_metadata_empty_results() -> None:
    ."""Test metadata with empty results."""
    from app.application.dto.pagination import PaginationMetadata

    metadata = PaginationMetadata.from_query(total_items=0, current_page=1, per_page=20)

    assert metadata.total_items == 0
    assert metadata.total_pages == 0
    assert metadata.current_page == 1
    assert metadata.per_page == 20
    assert metadata.has_next is False
    assert metadata.has_previous is False


def test_paginated_response_structure() -> None:
    ."""Test complete paginated response structure."""
    from app.application.dto.pagination import PaginatedResponseDTO, PaginationMetadata

    metadata = PaginationMetadata.from_query(total_items=10, current_page=1, per_page=5)

    response = PaginatedResponseDTO(
        items=[{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}],
        pagination=metadata,
        filters_applied={"marca": "Disano"},
        sorting_applied={"field": "precio", "order": "desc"},
    )

    assert len(response.items) == 5
    assert response.pagination.total_items == 10
    assert response.filters_applied == {"marca": "Disano"}
    assert response.sorting_applied == {"field": "precio", "order": "desc"}


def test_paginated_response_without_filters_sorting() -> None:
    """Test response without filters and sorting."""
    from app.application.dto.pagination import PaginatedResponseDTO, PaginationMetadata

    metadata = PaginationMetadata.from_query(total_items=10, current_page=1, per_page=5)

    response = PaginatedResponseDTO(items=[{"id": 1}, {"id": 2}], pagination=metadata)

    assert len(response.items) == 2
    assert response.filters_applied is None
    assert response.sorting_applied is None
