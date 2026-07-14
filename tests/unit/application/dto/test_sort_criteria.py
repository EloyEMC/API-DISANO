"""Tests for SortCriteria DTO."""

import pytest


def test_sort_criteria_default_sort() -> None:
    ."""Test default sorting is codigo asc."""
    from app.application.dto.pagination import SortCriteria

    criteria = SortCriteria(field="codigo", order="asc")

    assert criteria.field == "codigo"
    assert criteria.order == "asc"


def test_sort_criteria_order_normalization() -> None:
    """Test order is normalized to lowercase."""
    from app.application.dto.pagination import SortCriteria

    criteria = SortCriteria(field="pvp", order="DESC")

    assert criteria.field == "pvp"
    assert criteria.order == "desc"


def test_sort_criteria_field_validation() -> None:
    """Test invalid fields raise ValidationError."""
    from app.application.dto.pagination import SortCriteria
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        SortCriteria(field="invalid_field", order="asc")

    errors = exc_info.value.errors()
    assert any("field" in error["loc"] for error in errors)


def test_sort_criteria_allowed_fields() -> None:
    """Test all allowed fields work."""
    from app.application.dto.pagination import SortCriteria

    allowed_fields = [
        "codigo",
        "descripcion",
        "marca",
        "familia",
        "pvp",
        "bc3_descripcion_corta",
        "bc3_product_type",
    ]

    for field in allowed_fields:
        criteria = SortCriteria(field=field, order="asc")
        assert criteria.field == field
        assert criteria.order == "asc"
