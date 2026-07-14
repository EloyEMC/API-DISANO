"""Query parameter parser for V2 endpoints

Handles parsing, validation, and conversion of HTTP query parameters
into proper data structures for pagination, sorting, and filtering.
."""

from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
from enum import Enum


class SortDirection(str, Enum):
    """Valid sorting directions."""

    ASC = "asc"
    DESC = "desc"


@dataclass
class ParsedSortCriteria:
    """Parsed sort criteria from query parameter."""

    field: str
    direction: SortDirection = SortDirection.ASC

    @classmethod
    def from_string(cls, sort_string: str) -> "ParsedSortCriteria":
        """
        Parse sort string like 'field:asc' or 'field:desc'

        Args:
            sort_string: Sort string in format 'field:direction'

        Returns:
            ParsedSortCriteria object

        Raises:
            ValueError: If format is invalid
        ."""
        if not sort_string:
            raise ValueError("Sort string cannot be empty")

        parts = sort_string.split(":")
        field = parts[0].strip()

        if not field:
            raise ValueError("Sort field cannot be empty")

        direction = SortDirection.ASC
        if len(parts) > 1:
            direction_str = parts[1].strip().lower()
            try:
                direction = SortDirection(direction_str)
            except ValueError:
                raise ValueError(
                    f"Invalid sort direction: {direction_str}. Must be 'asc' or 'desc'"
                )

        return cls(field=field, direction=direction)

    def to_string(self) -> str:
        """Convert back to string format."""
        return f"{self.field}:{self.direction.value}"


@dataclass
class ParsedFilters:
    """Parsed filters from query parameters."""

    filters: Dict[str, Any]
    errors: List[str]

    def __init__(self):
        self.filters = {}
        self.errors = []

    def add_filter(self, key: str, value: Any, validator: Optional[callable] = None):
        """
        Add a filter with optional validation

        Args:
            key: Filter key
            value: Filter value
            validator: Optional validation function
        ."""
        if value is None:
            return

        try:
            if validator:
                validated_value = validator(value)
                self.filters[key] = validated_value
            else:
                self.filters[key] = value
        except ValueError as e:
            self.errors.append(f"Invalid filter '{key}': {str(e)}")

    def has_errors(self) -> bool:
        """Check if there are validation errors."""
        return len(self.errors) > 0

    def get_errors(self) -> List[str]:
        """Get validation errors."""
        return self.errors


class QueryParameterParser:
    """Parser for HTTP query parameters in V2 endpoints."""

    # Valid sort fields for different entity types
    VALID_SORT_FIELDS = {
        "productos": [
            "codigo",
            "descripcion",
            "marca",
            "familia",
            "pvp",
            "bc3_product_type",
            "bc3_descripcion_corta",
        ],
        "familias": [
            "nombre",
            "total_productos",
            "con_bc3",
            "con_imagen",
            "descontinuados",
        ],
        "bc3": [
            "codigo",
            "descripcion",
            "bc3_product_type",
            "bc3_descripcion_corta",
            "bc3_descripcion_completa",
        ],
    }

    # Valid filter operators
    VALID_OPERATORS = ["eq", "ne", "gt", "gte", "lt", "lte", "contains"]

    @classmethod
    def parse_sort_parameter(
        cls, sort_string: Optional[str], entity_type: str = "productos"
    ) -> Optional[ParsedSortCriteria]:
        """
        Parse sort parameter string

        Args:
            sort_string: Sort string (e.g., 'codigo:asc')
            entity_type: Type of entity for validation

        Returns:
            ParsedSortCriteria or None if sort_string is None

        Raises:
            ValueError: If sort field is invalid for entity type
        ."""
        if not sort_string:
            return None

        criteria = ParsedSortCriteria.from_string(sort_string)

        # Validate sort field
        valid_fields = cls.VALID_SORT_FIELDS.get(entity_type, [])
        if criteria.field not in valid_fields:
            raise ValueError(
                f"Invalid sort field '{criteria.field}' for {entity_type}. "
                f"Valid fields: {', '.join(valid_fields)}"
            )

        return criteria

    @classmethod
    def parse_filters(
        cls, query_params: Dict[str, Any], entity_type: str = "productos"
    ) -> ParsedFilters:
        """
        Parse query parameters into filters

        Args:
            query_params: Dictionary of query parameters
            entity_type: Type of entity for validation

        Returns:
            ParsedFilters object with filters and any validation errors
        ."""
        parsed = ParsedFilters()

        # Common filters
        if "buscar" in query_params and query_params["buscar"]:
            parsed.add_filter("buscar", query_params["buscar"], cls._validate_search_term)

        # Entity-specific filters
        if entity_type == "productos":
            cls._parse_producto_filters(query_params, parsed)
        elif entity_type == "familias":
            cls._parse_familia_filters(query_params, parsed)
        elif entity_type == "bc3":
            cls._parse_bc3_filters(query_params, parsed)

        return parsed

    @classmethod
    def _validate_search_term(cls, term: str) -> str:
        """Validate search term."""
        if not term or not term.strip():
            raise ValueError("Search term cannot be empty")
        return term.strip()

    @classmethod
    def _validate_price(cls, price: Union[str, float]) -> float:
        """Validate price parameter."""
        try:
            price_value = float(price) if isinstance(price, str) else price
            if price_value < 0:
                raise ValueError("Price cannot be negative")
            return price_value
        except (ValueError, TypeError):
            raise ValueError("Price must be a valid number")

    @classmethod
    def _validate_page_number(cls, page: Union[str, int]) -> int:
        """Validate page number."""
        try:
            page_value = int(page) if isinstance(page, str) else page
            if page_value < 1:
                raise ValueError("Page number must be at least 1")
            return page_value
        except (ValueError, TypeError):
            raise ValueError("Page number must be a valid integer")

    @classmethod
    def _validate_per_page(cls, per_page: Union[str, int]) -> int:
        """Validate per_page parameter."""
        try:
            per_page_value = int(per_page) if isinstance(per_page, str) else per_page
            if per_page_value < 1:
                raise ValueError("Per page must be at least 1")
            if per_page_value > 100:
                raise ValueError("Per page cannot exceed 100")
            return per_page_value
        except (ValueError, TypeError):
            raise ValueError("Per page must be a valid integer")

    @classmethod
    def _parse_producto_filters(cls, params: Dict[str, Any], parsed: ParsedFilters):
        """Parse product-specific filters."""
        if "marca" in params and params["marca"]:
            parsed.add_filter("marca", params["marca"])

        if "familia" in params and params["familia"]:
            parsed.add_filter("familia", params["familia"])

        if "pvp_min" in params and params["pvp_min"] is not None:
            parsed.add_filter("pvp_min", params["pvp_min"], cls._validate_price)

        if "pvp_max" in params and params["pvp_max"] is not None:
            parsed.add_filter("pvp_max", params["pvp_max"], cls._validate_price)

        if "bc3_product_type" in params and params["bc3_product_type"]:
            parsed.add_filter("bc3_product_type", params["bc3_product_type"])

        if (
            "bc3_has_descripcion_corta" in params
            and params["bc3_has_descripcion_corta"] is not None
        ):
            parsed.add_filter(
                "bc3_has_descripcion_corta",
                params["bc3_has_descripcion_corta"],
                lambda x: (
                    bool(x) if isinstance(x, bool) else bool(str(x).lower() in ("true", "1", "yes"))
                ),
            )

    @classmethod
    def _parse_familia_filters(cls, params: Dict[str, Any], parsed: ParsedFilters):
        """Parse familia-specific filters."""
        # Familia filters are mainly based on search term
        pass  # Currently familia only supports "buscar"

    @classmethod
    def _parse_bc3_filters(cls, params: Dict[str, Any], parsed: ParsedFilters):
        """Parse BC3-specific filters."""
        if "bc3_product_type" in params and params["bc3_product_type"]:
            parsed.add_filter("bc3_product_type", params["bc3_product_type"])

        if (
            "bc3_has_descripcion_corta" in params
            and params["bc3_has_descripcion_corta"] is not None
        ):
            parsed.add_filter(
                "bc3_has_descripcion_corta",
                params["bc3_has_descripcion_corta"],
                lambda x: (
                    bool(x) if isinstance(x, bool) else bool(str(x).lower() in ("true", "1", "yes"))
                ),
            )

        if (
            "bc3_has_descripcion_completa" in params
            and params["bc3_has_descripcion_completa"] is not None
        ):
            parsed.add_filter(
                "bc3_has_descripcion_completa",
                params["bc3_has_descripcion_completa"],
                lambda x: (
                    bool(x) if isinstance(x, bool) else bool(str(x).lower() in ("true", "1", "yes"))
                ),
            )

    @classmethod
    def parse_pagination_parameters(
        cls, page: Union[str, int] = 1, per_page: Union[str, int] = 20
    ) -> tuple[int, int]:
        """
        Parse and validate pagination parameters

        Args:
            page: Page number
            per_page: Items per page

        Returns:
            Tuple of (validated_page, validated_per_page)

        Raises:
            ValueError: If parameters are invalid
        ."""
        validated_page = cls._validate_page_number(page)
        validated_per_page = cls._validate_per_page(per_page)

        return validated_page, validated_per_page

    @classmethod
    def validate_all_parameters(
        cls, query_params: Dict[str, Any], entity_type: str = "productos"
    ) -> Dict[str, Any]:
        """
        Validate all query parameters

        Args:
            query_params: All query parameters
            entity_type: Type of entity for validation

        Returns:
            Dictionary with validated parameters

        Raises:
            ValueError: If any parameter is invalid
        ."""
        validated = {}

        # Validate pagination
        if "page" in query_params:
            validated["page"], validated["per_page"] = cls.parse_pagination_parameters(
                query_params.get("page", 1), query_params.get("per_page", 20)
            )

        # Validate sort
        if "sort" in query_params and query_params["sort"]:
            validated["sort_criteria"] = cls.parse_sort_parameter(query_params["sort"], entity_type)
            validated["sort"] = validated["sort_criteria"].to_string()

        # Validate filters
        parsed_filters = cls.parse_filters(query_params, entity_type)
        if parsed_filters.has_errors():
            raise ValueError(f"Filter validation errors: {'; '.join(parsed_filters.get_errors())}")
        validated["filters"] = parsed_filters.filters

        # Add remaining parameters
        for key, value in query_params.items():
            if key not in validated and not key.startswith("_"):
                validated[key] = value

        return validated
