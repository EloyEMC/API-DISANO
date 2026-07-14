"""Tests for FilterCriteria DTO."""

import pytest


def test_filter_criteria_all_optional() -> None:
    ."""Test all filter fields are optional."""
    from app.application.dto.pagination import FilterCriteria

    criteria = FilterCriteria()

    assert criteria.marca is None
    assert criteria.familia is None
    assert criteria.pvp_min is None
    assert criteria.pvp_max is None
    assert criteria.bc3_product_type is None
    assert criteria.bc3_has_descripcion_corta is None
    assert criteria.buscar is None


def test_filter_criteria_exact_match_filters() -> None:
    ."""Test exact match filters work."""
    from app.application.dto.pagination import FilterCriteria

    criteria = FilterCriteria(marca="Disano", familia="Iluminación", bc3_product_type="columna")

    assert criteria.marca == "Disano"
    assert criteria.familia == "Iluminación"
    assert criteria.bc3_product_type == "columna"


def test_filter_criteria_price_range_validation() -> None:
    """Test pvp_min >= 0 enforced."""
    from app.application.dto.pagination import FilterCriteria
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        FilterCriteria(pvp_min=-10)

    errors = exc_info.value.errors()
    assert any(
        "pvp_min" in error["loc"] and "greater than or equal to 0" in error["msg"]
        for error in errors
    )


def test_filter_criteria_price_range_invalid() -> None:
    """Test pvp_min <= pvp_max enforced."""
    from app.application.dto.pagination import FilterCriteria
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        FilterCriteria(pvp_min=100, pvp_max=50)

    errors = exc_info.value.errors()
    assert any("pvp_min cannot be greater than pvp_max" in error["msg"] for error in errors)


def test_filter_criteria_text_search() -> None:
    """Test text search field works."""
    from app.application.dto.pagination import FilterCriteria

    criteria = FilterCriteria(buscar="LED")

    assert criteria.buscar == "LED"


def test_filter_criteria_boolean_filter() -> None:
    """Test boolean filter works."""
    from app.application.dto.pagination import FilterCriteria

    criteria = FilterCriteria(bc3_has_descripcion_corta=True)

    assert criteria.bc3_has_descripcion_corta is True
