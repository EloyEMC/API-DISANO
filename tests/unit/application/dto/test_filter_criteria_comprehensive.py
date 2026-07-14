"""Comprehensive tests for FilterCriteria DTO."""

import pytest
from pydantic import ValidationError
from app.application.dto.pagination import FilterCriteria


def test_filter_criteria_all_optional() -> None:
    """Test all filter fields are optional."""
    criteria = FilterCriteria()

    assert criteria.marca is None
    assert criteria.familia is None
    assert criteria.pvp_min is None
    assert criteria.pvp_max is None
    assert criteria.bc3_product_type is None
    assert criteria.bc3_has_descripcion_corta is None
    assert criteria.buscar is None


def test_filter_criteria_exact_match_filters() -> None:
    """Test exact match filters work."""
    criteria = FilterCriteria(marca="Disano", familia="Iluminación", bc3_product_type="columna")

    assert criteria.marca == "Disano"
    assert criteria.familia == "Iluminación"
    assert criteria.bc3_product_type == "columna"


def test_filter_criteria_price_range_validation_lower_bound() -> None:
    """Test pvp_min >= 0 enforced."""
    with pytest.raises(ValidationError) as exc_info:
        FilterCriteria(pvp_min=-10)

    errors = exc_info.value.errors()
    assert any(
        "pvp_min" in error["loc"] and "greater than or equal to 0" in error["msg"]
        for error in errors
    )


def test_filter_criteria_price_range_validation_upper_bound() -> None:
    """Test pvp_max >= 0 enforced."""
    with pytest.raises(ValidationError) as exc_info:
        FilterCriteria(pvp_max=-5)

    errors = exc_info.value.errors()
    assert any(
        "pvp_max" in error["loc"] and "greater than or equal to 0" in error["msg"]
        for error in errors
    )


def test_filter_criteria_price_range_invalid() -> None:
    """Test pvp_min <= pvp_max enforced."""
    with pytest.raises(ValidationError) as exc_info:
        FilterCriteria(pvp_min=100, pvp_max=50)

    errors = exc_info.value.errors()
    assert any("pvp_min cannot be greater than pvp_max" in error["msg"] for error in errors)


def test_filter_criteria_price_range_valid() -> None:
    """Test valid price range works."""
    criteria = FilterCriteria(pvp_min=10, pvp_max=100)

    assert criteria.pvp_min == 10
    assert criteria.pvp_max == 100


def test_filter_criteria_price_range_equal_bounds() -> None:
    """Test price range with equal bounds works."""
    criteria = FilterCriteria(pvp_min=50, pvp_max=50)

    assert criteria.pvp_min == 50
    assert criteria.pvp_max == 50


def test_filter_criteria_price_range_zero() -> None:
    """Test price range starting at zero works."""
    criteria = FilterCriteria(pvp_min=0, pvp_max=50)

    assert criteria.pvp_min == 0
    assert criteria.pvp_max == 50


def test_filter_criteria_text_search() -> None:
    """Test text search field works."""
    criteria = FilterCriteria(buscar="LED")

    assert criteria.buscar == "LED"


def test_filter_criteria_boolean_filter_true() -> None:
    """Test boolean filter works with True."""
    criteria = FilterCriteria(bc3_has_descripcion_corta=True)

    assert criteria.bc3_has_descripcion_corta is True


def test_filter_criteria_boolean_filter_false() -> None:
    """Test boolean filter works with False."""
    criteria = FilterCriteria(bc3_has_descripcion_corta=False)

    assert criteria.bc3_has_descripcion_corta is False


def test_filter_criteria_single_filter() -> None:
    """Test single filter applied."""
    criteria = FilterCriteria(marca="Disano")

    assert criteria.marca == "Disano"
    assert criteria.familia is None
    assert criteria.pvp_min is None
    assert criteria.pvp_max is None


def test_filter_criteria_multiple_filters() -> None:
    """Test multiple filters applied."""
    criteria = FilterCriteria(
        marca="Disano",
        familia="Iluminación",
        pvp_min=10,
        pvp_max=100,
        bc3_product_type="columna",
        bc3_has_descripcion_corta=True,
        buscar="LED",
    )

    assert criteria.marca == "Disano"
    assert criteria.familia == "Iluminación"
    assert criteria.pvp_min == 10
    assert criteria.pvp_max == 100
    assert criteria.bc3_product_type == "columna"
    assert criteria.bc3_has_descripcion_corta is True
    assert criteria.buscar == "LED"


def test_filter_criteria_partial_filters() -> None:
    """Test partial filter application."""
    criteria = FilterCriteria(marca="Disano", pvp_min=50, bc3_has_descripcion_corta=False)

    assert criteria.marca == "Disano"
    assert criteria.familia is None  # Not specified
    assert criteria.pvp_min == 50
    assert criteria.pvp_max is None  # Not specified
    assert criteria.bc3_product_type is None  # Not specified
    assert criteria.bc3_has_descripcion_corta is False
    assert criteria.buscar is None  # Not specified


def test_filter_criteria_large_price_values() -> None:
    """Test large price values work."""
    criteria = FilterCriteria(pvp_min=0, pvp_max=1000000)

    assert criteria.pvp_min == 0
    assert criteria.pvp_max == 1000000


def test_filter_criteria_decimal_price_values() -> None:
    """Test decimal price values work."""
    criteria = FilterCriteria(pvp_min=9.99, pvp_max=199.95)

    assert criteria.pvp_min == 9.99
    assert criteria.pvp_max == 199.95


def test_filter_criteria_text_search_various_strings() -> None:
    """Test various text search strings."""
    search_terms = ["LED", "Iluminación", "Panel", "Downlight", "Bajo consumo"]

    for term in search_terms:
        criteria = FilterCriteria(buscar=term)
        assert criteria.buscar == term


def test_filter_criteria_text_search_validation() -> None:
    """Test that empty search string raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        FilterCriteria(buscar="")

    errors = exc_info.value.errors()
    assert any("buscar" in error["loc"] for error in errors)


def test_filter_criteria_text_search_with_spaces() -> None:
    """Test text search with spaces."""
    criteria = FilterCriteria(buscar="LED Panel 600x600")

    assert criteria.buscar == "LED Panel 600x600"


def test_filter_criteria_model_dump() -> None:
    """Test model_dump works correctly."""
    criteria = FilterCriteria(marca="Disano", familia="Iluminación", pvp_min=10, pvp_max=100)

    dump = criteria.model_dump()

    assert dump["marca"] == "Disano"
    assert dump["familia"] == "Iluminación"
    assert dump["pvp_min"] == 10
    assert dump["pvp_max"] == 100


def test_filter_criteria_model_dump_json() -> None:
    """Test model_dump_json works correctly."""
    criteria = FilterCriteria(marca="Fosnova", pvp_min=50)

    json_str = criteria.model_dump_json()

    assert '"marca":"Fosnova"' in json_str
    assert '"pvp_min":50' in json_str


def test_filter_criteria_model_validate() -> None:
    """Test model_validate works correctly."""
    data = {
        "marca": "Disano",
        "familia": "Iluminación",
        "pvp_min": 10,
        "pvp_max": 200,
    }
    criteria = FilterCriteria.model_validate(data)

    assert criteria.marca == "Disano"
    assert criteria.familia == "Iluminación"
    assert criteria.pvp_min == 10
    assert criteria.pvp_max == 200


def test_filter_criteria_typical_use_cases() -> None:
    """Test typical filter use cases."""
    # Brand filter
    brand_filter = FilterCriteria(marca="Disano")
    assert brand_filter.marca == "Disano"

    # Price range filter
    price_filter = FilterCriteria(pvp_min=50, pvp_max=200)
    assert price_filter.pvp_min == 50
    assert price_filter.pvp_max == 200

    # Text search filter
    search_filter = FilterCriteria(buscar="LED")
    assert search_filter.buscar == "LED"

    # BC3 coverage filter
    bc3_filter = FilterCriteria(bc3_has_descripcion_corta=True)
    assert bc3_filter.bc3_has_descripcion_corta is True

    # Combined filter
    combined_filter = FilterCriteria(
        marca="Disano",
        pvp_min=50,
        bc3_product_type="columna",
    )
    assert combined_filter.marca == "Disano"
    assert combined_filter.pvp_min == 50
    assert combined_filter.bc3_product_type == "columna"


def test_filter_criteria_edge_cases() -> None:
    """Test edge cases for FilterCriteria."""
    # Empty filters
    empty_filter = FilterCriteria()
    assert all(
        getattr(empty_filter, field) is None
        for field in [
            "marca",
            "familia",
            "pvp_min",
            "pvp_max",
            "bc3_product_type",
            "bc3_has_descripcion_corta",
            "buscar",
        ]
    )

    # Single price boundary
    single_price = FilterCriteria(pvp_min=100)
    assert single_price.pvp_min == 100
    assert single_price.pvp_max is None

    # Boolean variations
    bool_true = FilterCriteria(bc3_has_descripcion_corta=True)
    bool_false = FilterCriteria(bc3_has_descripcion_corta=False)
    assert bool_true.bc3_has_descripcion_corta is True
    assert bool_false.bc3_has_descripcion_corta is False


def test_filter_criteria_consistent_behavior() -> None:
    """Test that behavior is consistent across multiple instances."""
    criteria1 = FilterCriteria(marca="Disano", pvp_min=10)
    criteria2 = FilterCriteria(marca="Disano", pvp_min=10)

    assert criteria1.marca == criteria2.marca
    assert criteria1.pvp_min == criteria2.pvp_min


def test_filter_price_range_boundary_conditions() -> None:
    """Test boundary conditions for price range."""
    # Exactly at boundary
    criteria_exact = FilterCriteria(pvp_min=100, pvp_max=100)
    assert criteria_exact.pvp_min == 100
    assert criteria_exact.pvp_max == 100

    # Near boundary
    criteria_near = FilterCriteria(pvp_min=99.99, pvp_max=100.01)
    assert criteria_near.pvp_min == 99.99
    assert criteria_near.pvp_max == 100.01

    # Large range
    criteria_large = FilterCriteria(pvp_min=0, pvp_max=100000)
    assert criteria_large.pvp_min == 0
    assert criteria_large.pvp_max == 100000


def test_filter_criteria_comprehensive_filters() -> None:
    """Test comprehensive filter with all fields."""
    criteria = FilterCriteria(
        marca="Disano",
        familia="Iluminación",
        pvp_min=10.50,
        pvp_max=250.75,
        bc3_product_type="columna",
        bc3_has_descripcion_corta=True,
        buscar="LED",
    )

    assert criteria.marca == "Disano"
    assert criteria.familia == "Iluminación"
    assert criteria.pvp_min == 10.50
    assert criteria.pvp_max == 250.75
    assert criteria.bc3_product_type == "columna"
    assert criteria.bc3_has_descripcion_corta is True
    assert criteria.buscar == "LED"


def test_filter_criteria_various_data_types() -> None:
    """Test various data types for filters."""
    # String filters
    string_filter = FilterCriteria(marca="Test", familia="Family")
    assert isinstance(string_filter.marca, str)
    assert isinstance(string_filter.familia, str)

    # Numeric filters
    numeric_filter = FilterCriteria(pvp_min=50.50, pvp_max=100.75)
    assert isinstance(numeric_filter.pvp_min, float)
    assert isinstance(numeric_filter.pvp_max, float)

    # Boolean filters
    bool_filter = FilterCriteria(bc3_has_descripcion_corta=True)
    assert isinstance(bool_filter.bc3_has_descripcion_corta, bool)


def test_filter_criteria_flexible_combinations() -> None:
    """Test various combinations of filters."""
    combinations = [
        {"marca": "Disano"},
        {"familia": "Iluminación"},
        {"pvp_min": 10},
        {"pvp_max": 100},
        {"pvp_min": 10, "pvp_max": 100},
        {"marca": "Disano", "familia": "Iluminación"},
        {"pvp_min": 10, "bc3_product_type": "columna"},
        {"marca": "Disano", "buscar": "LED"},
        {
            "marca": "Disano",
            "familia": "Iluminación",
            "pvp_min": 10,
            "pvp_max": 100,
            "bc3_product_type": "columna",
            "bc3_has_descripcion_corta": True,
            "buscar": "LED",
        },
    ]

    for filter_data in combinations:
        criteria = FilterCriteria(**filter_data)
        for key, value in filter_data.items():
            assert getattr(criteria, key) == value
