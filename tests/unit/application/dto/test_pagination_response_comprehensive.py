"""Comprehensive tests for PaginatedResponseDTO and PaginationMetadata."""

from app.application.dto.pagination import PaginatedResponseDTO, PaginationMetadata


def test_pagination_metadata_from_query_calculation() -> None:
    """Test metadata calculation from query results."""
    metadata = PaginationMetadata.from_query(total_items=95, current_page=2, per_page=20)

    assert metadata.total_items == 95
    assert metadata.total_pages == 5
    assert metadata.current_page == 2
    assert metadata.per_page == 20
    assert metadata.has_next is True
    assert metadata.has_previous is True


def test_pagination_metadata_on_last_page() -> None:
    """Test metadata on last page."""
    metadata = PaginationMetadata.from_query(total_items=95, current_page=5, per_page=20)

    assert metadata.total_items == 95
    assert metadata.total_pages == 5
    assert metadata.current_page == 5
    assert metadata.per_page == 20
    assert metadata.has_next is False
    assert metadata.has_previous is True


def test_pagination_metadata_on_first_page() -> None:
    """Test metadata on first page."""
    metadata = PaginationMetadata.from_query(total_items=95, current_page=1, per_page=20)

    assert metadata.total_items == 95
    assert metadata.total_pages == 5
    assert metadata.current_page == 1
    assert metadata.per_page == 20
    assert metadata.has_next is True
    assert metadata.has_previous is False


def test_pagination_metadata_empty_results() -> None:
    """Test metadata with empty results."""
    metadata = PaginationMetadata.from_query(total_items=0, current_page=1, per_page=20)

    assert metadata.total_items == 0
    assert metadata.total_pages == 0
    assert metadata.current_page == 1
    assert metadata.per_page == 20
    assert metadata.has_next is False
    assert metadata.has_previous is False


def test_pagination_metadata_exact_page_count() -> None:
    """Test metadata when items exactly fill pages."""
    metadata = PaginationMetadata.from_query(total_items=100, current_page=2, per_page=20)

    assert metadata.total_items == 100
    assert metadata.total_pages == 5
    assert metadata.current_page == 2
    assert metadata.per_page == 20


def test_pagination_metadata_single_result() -> None:
    """Test metadata with single result."""
    metadata = PaginationMetadata.from_query(total_items=1, current_page=1, per_page=20)

    assert metadata.total_items == 1
    assert metadata.total_pages == 1
    assert metadata.current_page == 1
    assert metadata.per_page == 20
    assert metadata.has_next is False
    assert metadata.has_previous is False


def test_pagination_metadata_single_item_per_page() -> None:
    """Test metadata with single item per page."""
    metadata = PaginationMetadata.from_query(total_items=5, current_page=3, per_page=1)

    assert metadata.total_items == 5
    assert metadata.total_pages == 5
    assert metadata.current_page == 3
    assert metadata.per_page == 1
    assert metadata.has_next is True
    assert metadata.has_previous is True


def test_pagination_metadata_large_page_numbers() -> None:
    """Test metadata with large page numbers."""
    metadata = PaginationMetadata.from_query(total_items=10000, current_page=100, per_page=50)

    assert metadata.total_items == 10000
    assert metadata.total_pages == 200
    assert metadata.current_page == 100
    assert metadata.per_page == 50
    assert metadata.has_next is True
    assert metadata.has_previous is True


def test_pagination_metadata_model_dump() -> None:
    """Test model_dump works correctly."""
    metadata = PaginationMetadata.from_query(total_items=50, current_page=2, per_page=10)

    dump = metadata.model_dump()

    assert dump["total_items"] == 50
    assert dump["total_pages"] == 5
    assert dump["current_page"] == 2
    assert dump["per_page"] == 10
    assert dump["has_next"] is True
    assert dump["has_previous"] is True


def test_paginated_response_structure() -> None:
    """Test complete paginated response structure."""
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
    metadata = PaginationMetadata.from_query(total_items=10, current_page=1, per_page=5)

    response = PaginatedResponseDTO(items=[{"id": 1}, {"id": 2}], pagination=metadata)

    assert len(response.items) == 2
    assert response.filters_applied is None
    assert response.sorting_applied is None


def test_paginated_response_empty_items() -> None:
    """Test response with no items."""
    metadata = PaginationMetadata.from_query(total_items=0, current_page=1, per_page=20)

    response = PaginatedResponseDTO(items=[], pagination=metadata)

    assert len(response.items) == 0
    assert response.pagination.total_items == 0
    assert response.pagination.total_pages == 0


def test_paginated_response_single_item() -> None:
    """Test response with single item."""
    metadata = PaginationMetadata.from_query(total_items=1, current_page=1, per_page=20)

    response = PaginatedResponseDTO(
        items=[{"id": 1}], pagination=metadata, filters_applied={"marca": "Test"}
    )

    assert len(response.items) == 1
    assert response.pagination.total_items == 1
    assert response.filters_applied == {"marca": "Test"}


def test_paginated_response_multiple_filters() -> None:
    """Test response with multiple filters."""
    metadata = PaginationMetadata.from_query(total_items=25, current_page=1, per_page=10)

    response = PaginatedResponseDTO(
        items=[{"id": 1}, {"id": 2}],
        pagination=metadata,
        filters_applied={
            "marca": "Disano",
            "familia": "Iluminación",
            "pvp_min": 10,
            "pvp_max": 100,
        },
    )

    assert len(response.items) == 2
    assert len(response.filters_applied) == 4


def test_paginated_response_various_item_types() -> None:
    """Test response with different item types."""
    metadata = PaginationMetadata.from_query(total_items=3, current_page=1, per_page=10)

    # Test with dict items
    response_dict = PaginatedResponseDTO(items=[{"id": 1}, {"id": 2}], pagination=metadata)
    assert isinstance(response_dict.items[0], dict)

    # Test with string items
    response_str = PaginatedResponseDTO(items=["item1", "item2"], pagination=metadata)
    assert isinstance(response_str.items[0], str)

    # Test with number items
    response_num = PaginatedResponseDTO(items=[1, 2, 3], pagination=metadata)
    assert isinstance(response_num.items[0], int)


def test_paginated_response_model_dump() -> None:
    """Test model_dump works correctly."""
    metadata = PaginationMetadata.from_query(total_items=20, current_page=1, per_page=10)

    response = PaginatedResponseDTO(
        items=[{"id": 1}, {"id": 2}],
        pagination=metadata,
        filters_applied={"marca": "Test"},
    )

    dump = response.model_dump()

    assert len(dump["items"]) == 2
    assert dump["pagination"]["total_items"] == 20
    assert dump["filters_applied"] == {"marca": "Test"}


def test_paginated_response_model_dump_json() -> None:
    """Test model_dump_json works correctly."""
    metadata = PaginationMetadata.from_query(total_items=15, current_page=1, per_page=5)

    response = PaginatedResponseDTO(
        items=[{"id": 1}, {"id": 2}],
        pagination=metadata,
        sorting_applied={"field": "codigo", "order": "asc"},
    )

    json_str = response.model_dump_json()

    assert '"items":' in json_str
    assert '"total_items":15' in json_str
    assert '"field":"codigo"' in json_str
    assert '"order":"asc"' in json_str


def test_pagination_metadata_first_and_last_page_flags() -> None:
    """Test that first and last page flags are correct."""
    # First page
    metadata_first = PaginationMetadata.from_query(total_items=100, current_page=1, per_page=20)
    assert metadata_first.has_next is True
    assert metadata_first.has_previous is False

    # Middle page
    metadata_middle = PaginationMetadata.from_query(total_items=100, current_page=3, per_page=20)
    assert metadata_middle.has_next is True
    assert metadata_middle.has_previous is True

    # Last page
    metadata_last = PaginationMetadata.from_query(total_items=100, current_page=5, per_page=20)
    assert metadata_last.has_next is False
    assert metadata_last.has_previous is True


def test_pagination_metadata_fractional_pages() -> None:
    """Test metadata with fractional page count (rounding up)."""
    metadata = PaginationMetadata.from_query(total_items=95, current_page=1, per_page=20)

    assert metadata.total_items == 95
    assert metadata.total_pages == 5  # 95/20 = 4.75, rounded up to 5


def test_pagination_metadata_per_page_variations() -> None:
    """Test metadata with different per_page values."""
    per_page_values = [1, 10, 20, 50, 100]

    for per_page in per_page_values:
        metadata = PaginationMetadata.from_query(total_items=100, current_page=1, per_page=per_page)
        assert metadata.per_page == per_page
        expected_pages = (100 + per_page - 1) // per_page  # Ceiling division
        assert metadata.total_pages == expected_pages


def test_paginated_response_comprehensive_structure() -> None:
    """Test comprehensive response structure with all fields."""
    metadata = PaginationMetadata.from_query(total_items=50, current_page=2, per_page=10)

    response = PaginatedResponseDTO(
        items=[
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
        ],
        pagination=metadata,
        filters_applied={
            "marca": "Disano",
            "familia": "Iluminación",
            "pvp_min": 50,
            "pvp_max": 200,
            "buscar": "LED",
        },
        sorting_applied={"field": "precio", "order": "desc"},
    )

    assert len(response.items) == 2
    assert response.pagination.total_items == 50
    assert response.pagination.total_pages == 5
    assert len(response.filters_applied) == 5
    assert response.sorting_applied["field"] == "precio"
    assert response.sorting_applied["order"] == "desc"


def test_pagination_metadata_single_item_last_page() -> None:
    """Test metadata when single item and it's the last page."""
    metadata = PaginationMetadata.from_query(total_items=1, current_page=1, per_page=10)

    assert metadata.total_items == 1
    assert metadata.total_pages == 1
    assert metadata.has_next is False
    assert metadata.has_previous is False
