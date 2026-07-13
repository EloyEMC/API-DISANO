"""Comprehensive tests for PaginationRequestDTO."""

import pytest
from pydantic import ValidationError
from app.application.dto.pagination import PaginationRequestDTO


def test_pagination_request_default_values() -> None:
    """Test default values for pagination request."""
    dto = PaginationRequestDTO(page=1, per_page=20)

    assert dto.page == 1
    assert dto.per_page == 20
    assert dto.sort is None


def test_pagination_request_custom_values() -> None:
    """Test custom values for pagination request."""
    dto = PaginationRequestDTO(page=5, per_page=50, sort="precio:desc")

    assert dto.page == 5
    assert dto.per_page == 50
    assert dto.sort == "precio:desc"


def test_pagination_request_offset_calculation_page_1() -> None:
    """Test offset calculation for first page."""
    dto = PaginationRequestDTO(page=1, per_page=10)
    assert dto.offset == 0  # (1-1) * 10


def test_pagination_request_offset_calculation_page_3() -> None:
    """Test offset calculation for middle page."""
    dto = PaginationRequestDTO(page=3, per_page=10)
    assert dto.offset == 20  # (3-1) * 10


def test_pagination_request_offset_calculation_large_page() -> None:
    """Test offset calculation for large page number."""
    dto = PaginationRequestDTO(page=100, per_page=25)
    assert dto.offset == 2475  # (100-1) * 25


def test_pagination_request_offset_calculation_per_page_1() -> None:
    """Test offset calculation with per_page=1."""
    dto = PaginationRequestDTO(page=5, per_page=1)
    assert dto.offset == 4  # (5-1) * 1


def test_pagination_request_page_validation_zero() -> None:
    """Test that page < 1 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PaginationRequestDTO(page=0, per_page=20)

    errors = exc_info.value.errors()
    assert any(
        "page" in error["loc"] and "greater than or equal to 1" in error["msg"]
        for error in errors
    )


def test_pagination_request_page_validation_negative() -> None:
    """Test that negative page raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PaginationRequestDTO(page=-5, per_page=20)

    errors = exc_info.value.errors()
    assert any(
        "page" in error["loc"] and "greater than or equal to 1" in error["msg"]
        for error in errors
    )


def test_pagination_request_per_page_validation_upper_bound() -> None:
    """Test that per_page > 100 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PaginationRequestDTO(page=1, per_page=101)

    errors = exc_info.value.errors()
    assert any(
        "per_page" in error["loc"] and "less than or equal to 100" in error["msg"]
        for error in errors
    )


def test_pagination_request_per_page_validation_lower_bound() -> None:
    """Test that per_page < 1 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PaginationRequestDTO(page=1, per_page=0)

    errors = exc_info.value.errors()
    assert any(
        "per_page" in error["loc"] and "greater than or equal to 1" in error["msg"]
        for error in errors
    )


def test_pagination_request_per_page_boundary_values() -> None:
    """Test boundary values for per_page."""
    # Lower boundary
    dto_min = PaginationRequestDTO(page=1, per_page=1)
    assert dto_min.per_page == 1

    # Upper boundary
    dto_max = PaginationRequestDTO(page=1, per_page=100)
    assert dto_max.per_page == 100


def test_pagination_request_sort_none() -> None:
    """Test that sort can be None."""
    dto = PaginationRequestDTO(page=1, per_page=20, sort=None)
    assert dto.sort is None


def test_pagination_request_sort_with_field_only() -> None:
    """Test sort with field only (no order specified)."""
    dto = PaginationRequestDTO(page=1, per_page=20, sort="precio")
    assert dto.sort == "precio"


def test_pagination_request_sort_with_field_and_order() -> None:
    """Test sort with field and order specified."""
    dto = PaginationRequestDTO(page=1, per_page=20, sort="precio:desc")
    assert dto.sort == "precio:desc"


def test_pagination_request_sort_various_fields() -> None:
    """Test sorting by various fields."""
    sort_fields = [
        "codigo:asc",
        "descripcion:desc",
        "marca:asc",
        "familia:desc",
        "pvp:asc",
        "bc3_descripcion_corta:desc",
    ]

    for sort_field in sort_fields:
        dto = PaginationRequestDTO(page=1, per_page=20, sort=sort_field)
        assert dto.sort == sort_field


def test_pagination_request_is_mutable() -> None:
    """Test that DTO is mutable (Pydantic v2 default behavior)."""
    dto = PaginationRequestDTO(page=1, per_page=20, sort="precio:asc")

    # Should be able to modify values in Pydantic v2
    dto.page = 2
    assert dto.page == 2


def test_pagination_request_model_dump() -> None:
    """Test model_dump works correctly."""
    dto = PaginationRequestDTO(page=3, per_page=25, sort="precio:desc")

    dump = dto.model_dump()

    assert dump["page"] == 3
    assert dump["per_page"] == 25
    assert dump["sort"] == "precio:desc"


def test_pagination_request_model_dump_json() -> None:
    """Test model_dump_json works correctly."""
    dto = PaginationRequestDTO(page=2, per_page=30, sort="codigo:asc")

    json_str = dto.model_dump_json()

    assert '"page":2' in json_str
    assert '"per_page":30' in json_str
    assert '"sort":"codigo:asc"' in json_str


def test_pagination_request_model_validate() -> None:
    """Test model_validate works correctly."""
    data = {"page": 4, "per_page": 15, "sort": "familia:desc"}
    dto = PaginationRequestDTO.model_validate(data)

    assert dto.page == 4
    assert dto.per_page == 15
    assert dto.sort == "familia:desc"


def test_pagination_request_string_sort_formats() -> None:
    """Test various string sort formats."""
    # With colon separator
    dto1 = PaginationRequestDTO(page=1, per_page=20, sort="precio:asc")
    assert dto1.sort == "precio:asc"

    # Single field (no colon)
    dto2 = PaginationRequestDTO(page=1, per_page=20, sort="precio")
    assert dto2.sort == "precio"

    # Multiple characters
    dto3 = PaginationRequestDTO(page=1, per_page=20, sort="bc3_descripcion_corta:desc")
    assert dto3.sort == "bc3_descripcion_corta:desc"


def test_pagination_request_large_values() -> None:
    """Test DTO can handle large numeric values."""
    dto = PaginationRequestDTO(page=1000, per_page=100)
    assert dto.offset == 99900  # (1000-1) * 100


def test_pagination_request_typical_use_case() -> None:
    """Test typical use case for first page."""
    dto = PaginationRequestDTO(page=1, per_page=20)

    assert dto.page == 1
    assert dto.per_page == 20
    assert dto.offset == 0
    assert dto.sort is None
