"""Tests for PaginationRequestDTO."""

import pytest
from pydantic import ValidationError


def test_pagination_request_default_values() -> None:
    ."""Test default values for pagination request."""
    from app.application.dto.pagination import PaginationRequestDTO

    dto = PaginationRequestDTO(page=1, per_page=20)

    assert dto.page == 1
    assert dto.per_page == 20
    assert dto.sort is None


def test_pagination_request_offset_calculation() -> None:
    ."""Test offset calculation from page and per_page."""
    from app.application.dto.pagination import PaginationRequestDTO

    dto = PaginationRequestDTO(page=3, per_page=10)

    assert dto.offset == 20  # (3-1) * 10


def test_pagination_request_page_validation() -> None:
    ."""Test that page < 1 raises ValidationError."""
    from app.application.dto.pagination import PaginationRequestDTO

    with pytest.raises(ValidationError) as exc_info:
        PaginationRequestDTO(page=0, per_page=20)

    errors = exc_info.value.errors()
    assert any(
        "page" in error["loc"] and "greater than or equal to 1" in error["msg"] for error in errors
    )


def test_pagination_request_per_page_validation() -> None:
    """Test that per_page > 100 raises ValidationError."""
    from app.application.dto.pagination import PaginationRequestDTO

    with pytest.raises(ValidationError) as exc_info:
        PaginationRequestDTO(page=1, per_page=101)

    errors = exc_info.value.errors()
    assert any(
        "per_page" in error["loc"] and "less than or equal to 100" in error["msg"]
        for error in errors
    )
