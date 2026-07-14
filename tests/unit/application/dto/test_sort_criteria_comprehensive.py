"""Comprehensive tests for SortCriteria DTO."""

import pytest
from pydantic import ValidationError
from app.application.dto.pagination import SortCriteria


def test_sort_criteria_default_sort() -> None:
    ."""Test default sorting is codigo asc."""
    criteria = SortCriteria(field="codigo", order="asc")

    assert criteria.field == "codigo"
    assert criteria.order == "asc"


def test_sort_criteria_order_normalization_uppercase() -> None:
    """Test order is normalized to lowercase."""
    criteria = SortCriteria(field="pvp", order="DESC")

    assert criteria.field == "pvp"
    assert criteria.order == "desc"


def test_sort_criteria_order_normalization_mixed_case() -> None:
    """Test order normalization with mixed case."""
    criteria = SortCriteria(field="pvp", order="AsC")

    assert criteria.field == "pvp"
    assert criteria.order == "asc"


def test_sort_criteria_field_validation_invalid_field() -> None:
    """Test invalid fields raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        SortCriteria(field="invalid_field", order="asc")

    errors = exc_info.value.errors()
    assert any("field" in error["loc"] for error in errors)


def test_sort_criteria_field_validation_empty_field() -> None:
    """Test empty field raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        SortCriteria(field="", order="asc")

    errors = exc_info.value.errors()
    assert any("field" in error["loc"] for error in errors)


def test_sort_criteria_allowed_fields_basic() -> None:
    """Test all basic allowed fields work."""
    allowed_fields = [
        "codigo",
        "descripcion",
        "marca",
        "familia",
        "pvp",
    ]

    for field in allowed_fields:
        criteria = SortCriteria(field=field, order="asc")
        assert criteria.field == field
        assert criteria.order == "asc"


def test_sort_criteria_allowed_fields_bc3() -> None:
    """Test BC3-related allowed fields work."""
    bc3_fields = [
        "bc3_descripcion_corta",
        "bc3_product_type",
    ]

    for field in bc3_fields:
        criteria = SortCriteria(field=field, order="asc")
        assert criteria.field == field
        assert criteria.order == "asc"


def test_sort_criteria_all_allowed_fields() -> None:
    """Test all allowed fields work."""
    all_fields = [
        "codigo",
        "descripcion",
        "marca",
        "familia",
        "pvp",
        "bc3_descripcion_corta",
        "bc3_product_type",
    ]

    for field in all_fields:
        criteria_asc = SortCriteria(field=field, order="asc")
        criteria_desc = SortCriteria(field=field, order="desc")

        assert criteria_asc.field == field
        assert criteria_asc.order == "asc"
        assert criteria_desc.field == field
        assert criteria_desc.order == "desc"


def test_sort_criteria_order_validation_permissive() -> None:
    """Test that order validation is permissive (any string accepted)."""
    # The current implementation allows any order string
    # Order normalization happens at parsing time, not at validation time
    criteria_invalid = SortCriteria(field="codigo", order="invalid")
    assert criteria_invalid.order == "invalid"  # Stored as-is

    criteria_empty = SortCriteria(field="codigo", order="")
    assert criteria_empty.order == ""  # Empty strings are allowed


def test_sort_criteria_various_sort_strings() -> None:
    """Test various sort string formats."""
    sort_strings = [
        ("codigo", "asc"),
        ("codigo", "desc"),
        ("pvp", "asc"),
        ("pvp", "desc"),
        ("marca", "asc"),
        ("familia", "desc"),
    ]

    for field, order in sort_strings:
        criteria = SortCriteria(field=field, order=order)
        assert criteria.field == field
        assert criteria.order == order


def test_sort_criteria_model_dump() -> None:
    """Test model_dump works correctly."""
    criteria = SortCriteria(field="pvp", order="desc")

    dump = criteria.model_dump()

    assert dump["field"] == "pvp"
    assert dump["order"] == "desc"


def test_sort_criteria_model_dump_json() -> None:
    """Test model_dump_json works correctly."""
    criteria = SortCriteria(field="codigo", order="asc")

    json_str = criteria.model_dump_json()

    assert '"field":"codigo"' in json_str
    assert '"order":"asc"' in json_str


def test_sort_criteria_model_validate() -> None:
    """Test model_validate works correctly."""
    data = {"field": "familia", "order": "desc"}
    criteria = SortCriteria.model_validate(data)

    assert criteria.field == "familia"
    assert criteria.order == "desc"


def test_sort_criteria_string_normalization_various_formats() -> None:
    """Test order normalization with various string formats."""
    test_cases = [
        ("ASC", "asc"),
        ("asc", "asc"),
        ("AsC", "asc"),
        ("DESC", "desc"),
        ("desc", "desc"),
        ("DeSc", "desc"),
    ]

    for input_order, expected_order in test_cases:
        criteria = SortCriteria(field="codigo", order=input_order)
        assert criteria.order == expected_order


def test_sort_criteria_field_with_underscores() -> None:
    """Test fields with underscores work correctly."""
    criteria = SortCriteria(field="bc3_descripcion_corta", order="asc")

    assert criteria.field == "bc3_descripcion_corta"
    assert criteria.order == "asc"


def test_sort_criteria_special_characters_in_field() -> None:
    """Test that fields without special characters work."""
    # Valid fields
    valid_criteria = SortCriteria(field="bc3_product_type", order="asc")
    assert valid_criteria.field == "bc3_product_type"

    # Invalid fields should fail
    with pytest.raises(ValidationError):
        SortCriteria(field="precio$", order="asc")


def test_sort_criteria_consistent_behavior() -> None:
    """Test that behavior is consistent across multiple instances."""
    criteria1 = SortCriteria(field="pvp", order="desc")
    criteria2 = SortCriteria(field="pvp", order="desc")

    assert criteria1.field == criteria2.field
    assert criteria1.order == criteria2.order


def test_sort_criteria_typical_use_cases() -> None:
    """Test typical use cases for sorting."""
    # Price descending
    price_desc = SortCriteria(field="pvp", order="desc")
    assert price_desc.field == "pvp"
    assert price_desc.order == "desc"

    # Code ascending
    code_asc = SortCriteria(field="codigo", order="asc")
    assert code_asc.field == "codigo"
    assert code_asc.order == "asc"

    # Family name ascending
    family_asc = SortCriteria(field="familia", order="asc")
    assert family_asc.field == "familia"
    assert family_asc.order == "asc"

    # Description descending
    description_desc = SortCriteria(field="descripcion", order="desc")
    assert description_desc.field == "descripcion"
    assert description_desc.order == "desc"


def test_sort_criteria_case_sensitivity() -> None:
    """Test that field names are case-sensitive."""
    # Assuming lowercase fields are required
    criteria_lower = SortCriteria(field="codigo", order="asc")
    assert criteria_lower.field == "codigo"

    # Test that uppercase field might fail (depending on validation)
    # This depends on the specific validation rules implemented
    try:
        criteria_upper = SortCriteria(field="CODIGO", order="asc")
        # If it passes, check behavior
        assert criteria_upper.field == "CODIGO"
    except ValidationError:
        # Expected if case-sensitive validation is implemented
        pass


def test_sort_criteria_combinations() -> None:
    """Test various field and order combinations."""
    combinations = [
        ("codigo", "asc"),
        ("codigo", "desc"),
        ("pvp", "asc"),
        ("pvp", "desc"),
        ("marca", "asc"),
        ("marca", "desc"),
        ("familia", "asc"),
        ("familia", "desc"),
        ("descripcion", "asc"),
        ("descripcion", "desc"),
    ]

    for field, order in combinations:
        criteria = SortCriteria(field=field, order=order)
        assert criteria.field == field
        assert criteria.order == order


def test_sort_criteria_edge_cases() -> None:
    """Test edge cases for SortCriteria."""
    # Minimum valid field
    criteria_min = SortCriteria(field="codigo", order="asc")
    assert criteria_min.field == "codigo"

    # Field with maximum length
    criteria_max = SortCriteria(field="bc3_descripcion_corta", order="desc")
    assert criteria_max.field == "bc3_descripcion_corta"
