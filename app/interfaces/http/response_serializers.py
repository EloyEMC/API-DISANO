"""Response serializers for V2 endpoints

Handles conversion of domain entities to API response DTOs,
JSON serialization, and formatting for consistent API responses.
."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from decimal import Decimal
import json


class ResponseSerializer:
    """Serializer for converting domain entities to API responses."""

    # Fields to exclude from different entity types
    EXCLUDED_FIELDS = {
        "producto": ["id", "internal_fields"],
        "familia": ["internal_fields"],
        "bc3": ["raw_data"],
    }

    @classmethod
    def serialize_entity(
        cls,
        entity: Any,
        entity_type: str = "producto",
        exclude_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Serialize a domain entity to a dictionary

        Args:
            entity: Domain entity to serialize
            entity_type: Type of entity for field filtering
            exclude_fields: Additional fields to exclude

        Returns:
            Serialized entity as dictionary
        ."""
        if entity is None:
            return {}

        # Convert entity to dict if it has model_dump method
        if hasattr(entity, "model_dump"):
            data = entity.model_dump()
        elif hasattr(entity, "dict"):
            data = entity.dict()
        elif isinstance(entity, dict):
            data = entity.copy()
        else:
            data = vars(entity)

        # Apply exclusion filters
        excluded = cls.EXCLUDED_FIELDS.get(entity_type, [])
        if exclude_fields:
            excluded.extend(exclude_fields)

        # Remove excluded fields
        for field in excluded:
            data.pop(field, None)

        # Clean None values
        data = {k: v for k, v in data.items() if v is not None}

        return data

    @classmethod
    def serialize_entities(
        cls,
        entities: List[Any],
        entity_type: str = "producto",
        exclude_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Serialize a list of domain entities

        Args:
            entities: List of domain entities to serialize
            entity_type: Type of entity for field filtering
            exclude_fields: Additional fields to exclude

        Returns:
            List of serialized entities as dictionaries
        ."""
        return [cls.serialize_entity(entity, entity_type, exclude_fields) for entity in entities]

    @classmethod
    def serialize_pagination_metadata(cls, metadata: Any) -> Dict[str, Any]:
        """
        Serialize pagination metadata

        Args:
            metadata: Pagination metadata object

        Returns:
            Serialized pagination metadata
        ."""
        if hasattr(metadata, "model_dump"):
            return metadata.model_dump()
        elif hasattr(metadata, "dict"):
            return metadata.dict()
        elif isinstance(metadata, dict):
            return metadata.copy()
        else:
            return vars(metadata)

    @classmethod
    def serialize_paginated_response(
        cls, paginated_response: Any, entity_type: str = "producto"
    ) -> Dict[str, Any]:
        """
        Serialize a paginated response with entities and metadata

        Args:
            paginated_response: PaginatedResponseDTO object
            entity_type: Type of entity for field filtering

        Returns:
            Serialized paginated response
        ."""
        # Serialize items
        if hasattr(paginated_response, "items"):
            items = cls.serialize_entities(paginated_response.items, entity_type)
        else:
            items = []

        # Serialize pagination metadata
        if hasattr(paginated_response, "pagination"):
            pagination = cls.serialize_pagination_metadata(paginated_response.pagination)
        else:
            pagination = {}

        # Get filters and sorting applied
        filters_applied = getattr(paginated_response, "filters_applied", {})
        sorting_applied = getattr(paginated_response, "sorting_applied", None)

        return {
            "items": items,
            "pagination": pagination,
            "filters_applied": filters_applied,
            "sorting_applied": sorting_applied,
        }

    @classmethod
    def format_for_json(cls, data: Any, indent: int = 2) -> str:
        """
        Format data as JSON string with custom formatting

        Args:
            data: Data to format
            indent: Indentation level

        Returns:
            JSON string
        ."""

        def json_serializer(obj):
            """Custom JSON serializer for special types."""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Decimal):
                return float(obj)
            elif hasattr(obj, "model_dump"):
                return obj.model_dump()
            elif hasattr(obj, "__dict__"):
                return obj.__dict__
            else:
                return str(obj)

        return json.dumps(data, default=json_serializer, indent=indent)

    @classmethod
    def create_success_response(
        cls,
        data: Any,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized success response

        Args:
            data: Response data
            message: Optional success message
            metadata: Optional metadata

        Returns:
            Standardized success response
        ."""
        response = {
            "success": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if message:
            response["message"] = message

        if metadata:
            response["metadata"] = metadata

        return response

    @classmethod
    def create_error_response(
        cls,
        error: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a standardized error response

        Args:
            error: Error message
            details: Optional error details
            error_code: Optional error code

        Returns:
            Standardized error response
        ."""
        response = {
            "success": False,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if details:
            response["details"] = details

        if error_code:
            response["error_code"] = error_code

        return response

    @classmethod
    def filter_sensitive_fields(
        cls, data: Dict[str, Any], sensitive_fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Filter out sensitive fields from response data

        Args:
            data: Data to filter
            sensitive_fields: List of sensitive field names

        Returns:
            Filtered data
        ."""
        if sensitive_fields is None:
            sensitive_fields = []

        filtered_data = data.copy()
        for field in sensitive_fields:
            if field in filtered_data:
                filtered_data[field] = "***REDACTED***"

        return filtered_data

    @classmethod
    def format_currency(cls, value: Optional[float], currency: str = "EUR") -> str:
        """
        Format a value as currency

        Args:
            value: Numeric value to format
            currency: Currency code

        Returns:
            Formatted currency string
        ."""
        if value is None:
            return f"N/A {currency}"

        return f"{value:.2f} {currency}"

    @classmethod
    def format_percentage(cls, value: Optional[float], decimals: int = 2) -> str:
        """
        Format a value as percentage

        Args:
            value: Numeric value to format
            decimals: Number of decimal places

        Returns:
            Formatted percentage string
        ."""
        if value is None:
            return "N/A"

        return f"{value:.{decimals}f}%"


class ProductoResponseSerializer(ResponseSerializer):
    """Serializer specific to Producto entities."""

    PRODUCTO_FIELDS_ORDER = [
        "codigo",
        "descripcion",
        "marca",
        "familia",
        "pvp",
        "bc3_descripcion_corta",
        "bc3_product_type",
        "imagen_url",
    ]

    @classmethod
    def serialize_producto(cls, producto: Any, detailed: bool = False) -> Dict[str, Any]:
        """
        Serialize a producto entity with field ordering

        Args:
            producto: Producto entity to serialize
            detailed: Whether to include detailed fields

        Returns:
            Serialized producto with ordered fields
        ."""
        data = cls.serialize_entity(producto, "producto")

        if not detailed:
            # Keep only essential fields for list views
            essential_fields = {
                "codigo": data.get("codigo"),
                "descripcion": data.get("descripcion"),
                "marca": data.get("marca"),
                "familia": data.get("familia"),
                "pvp": data.get("pvp"),
                "bc3_product_type": data.get("bc3_product_type"),
                "imagen_url": data.get("imagen_url"),
            }
            return {k: v for k, v in essential_fields.items() if v is not None}

        return data

    @classmethod
    def serialize_productos_list(
        cls, productos: List[Any], detailed: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Serialize a list of productos

        Args:
            productos: List of producto entities
            detailed: Whether to include detailed fields

        Returns:
            List of serialized productos
        ."""
        return [cls.serialize_producto(p, detailed) for p in productos]


class FamiliaResponseSerializer(ResponseSerializer):
    """Serializer specific to Familia entities."""

    @classmethod
    def serialize_familia(cls, familia: Any) -> Dict[str, Any]:
        """
        Serialize a familia entity with BC3 coverage

        Args:
            familia: Familia entity to serialize

        Returns:
            Serialized familia with BC3 statistics
        ."""
        data = cls.serialize_entity(familia, "familia")

        # Calculate BC3 coverage percentage if not present
        if "bc3_coverage_percentage" not in data:
            total = data.get("total_productos", 0)
            con_bc3 = data.get("con_bc3", 0)
            if total > 0:
                data["bc3_coverage_percentage"] = round((con_bc3 / total) * 100, 2)
            else:
                data["bc3_coverage_percentage"] = 0.0

        return data

    @classmethod
    def serialize_familias_list(cls, familias: List[Any]) -> List[Dict[str, Any]]:
        """
        Serialize a list of familias with BC3 coverage

        Args:
            familias: List of familia entities

        Returns:
            List of serialized familias
        ."""
        return [cls.serialize_familia(f) for f in familias]


class BC3ResponseSerializer(ResponseSerializer):
    """Serializer specific to BC3 data."""

    @classmethod
    def serialize_bc3_stats(cls, stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize BC3 statistics with formatted percentages

        Args:
            stats: BC3 statistics dictionary

        Returns:
            Formatted BC3 statistics
        ."""
        formatted_stats = stats.copy()

        # Format percentages if present
        if "porcentajes" in formatted_stats:
            for key, value in formatted_stats["porcentajes"].items():
                if isinstance(value, (int, float)):
                    formatted_stats["porcentajes"][key] = f"{value:.2f}%"

        return formatted_stats

    @classmethod
    def serialize_bc3_producto(cls, producto: Any) -> Dict[str, Any]:
        """
        Serialize a producto with BC3-specific fields

        Args:
            producto: Producto entity with BC3 data

        Returns:
            Serialized producto with BC3 focus
        ."""
        data = cls.serialize_entity(producto, "producto")

        # Focus on BC3 fields
        bc3_fields = {
            "codigo": data.get("codigo"),
            "bc3_descripcion_corta": data.get("bc3_descripcion_corta"),
            "bc3_descripcion_completa": data.get("bc3_descripcion_completa"),
            "bc3_product_type": data.get("bc3_product_type"),
            "bc3_processed_at": data.get("bc3_processed_at"),
        }

        # Add essential fields for context
        bc3_fields["descripcion"] = data.get("descripcion")
        bc3_fields["marca"] = data.get("marca")

        return bc3_fields
