"""Custom exceptions for API-DISANO V2 endpoints

Provides domain-specific exceptions with proper HTTP status codes
and error message formatting.
."""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""

    # General errors (4xx)
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNPROCESSABLE_ENTITY = "UNPROCESSABLE_ENTITY"

    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"

    # Domain-specific errors
    INVALID_PAGE = "INVALID_PAGE"
    INVALID_PER_PAGE = "INVALID_PER_PAGE"
    INVALID_SORT_FIELD = "INVALID_SORT_FIELD"
    INVALID_SORT_DIRECTION = "INVALID_SORT_DIRECTION"
    INVALID_FILTER = "INVALID_FILTER"
    INVALID_PRICE_RANGE = "INVALID_PRICE_RANGE"

    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    PRODUCT_INVALID = "PRODUCT_INVALID"
    FAMILIA_NOT_FOUND = "FAMILIA_NOT_FOUND"
    BC3_DATA_INVALID = "BC3_DATA_INVALID"

    CACHE_MISS = "CACHE_MISS"
    CACHE_INVALIDATION_ERROR = "CACHE_INVALIDATION_ERROR"


class APIException(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize API exception

        Args:
            message: Human-readable error message
            error_code: Standardized error code
            status_code: HTTP status code
            details: Additional error details
            context: Request context for debugging
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.context = context or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        error_dict = {
            "error": self.message,
            "error_code": self.error_code.value,
            "status_code": self.status_code,
            "timestamp": datetime_utc_now(),
        }

        if self.details:
            error_dict["details"] = self.details

        if self.context:
            error_dict["context"] = self.context

        return error_dict


def datetime_utc_now():
    """Get current UTC datetime as ISO string."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


# ==============================================================================
# 4xx Client Errors
# ==============================================================================


class BadRequestException(APIException):
    """Bad Request (400) - Invalid request parameters."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.BAD_REQUEST,
            status_code=400,
            details=details,
        )


class UnauthorizedException(APIException):
    """Unauthorized (401) - Authentication required."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, error_code=ErrorCode.UNAUTHORIZED, status_code=401)


class ForbiddenException(APIException):
    """Forbidden (403) - Insufficient permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, error_code=ErrorCode.FORBIDDEN, status_code=403)


class NotFoundException(APIException):
    """Not Found (404) - Resource not found."""

    def __init__(self, message: str, resource_type: Optional[str] = None):
        details = {"resource_type": resource_type} if resource_type else None
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            details=details,
        )


class ConflictException(APIException):
    """Conflict (409) - Resource conflict."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFLICT,
            status_code=409,
            details=details,
        )


class ValidationException(APIException):
    """Validation Error (422) - Invalid data format."""

    def __init__(self, message: str, validation_errors: Optional[Dict[str, Any]] = None):
        details = {"validation_errors": validation_errors} if validation_errors else None
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details=details,
        )


# ==============================================================================
# Domain-Specific Validation Errors
# ==============================================================================


class PaginationException(APIException):
    """Pagination parameter errors."""

    def __init__(
        self,
        message: str,
        parameter_name: str,
        invalid_value: Any,
        valid_range: Optional[str] = None,
    ):
        details = {
            "parameter": parameter_name,
            "invalid_value": str(invalid_value),
            "valid_range": valid_range,
        }

        if parameter_name == "page":
            error_code = ErrorCode.INVALID_PAGE
        elif parameter_name == "per_page":
            error_code = ErrorCode.INVALID_PER_PAGE
        else:
            error_code = ErrorCode.VALIDATION_ERROR

        super().__init__(message=message, error_code=error_code, status_code=400, details=details)


class SortException(APIException):
    """Sorting parameter errors."""

    def __init__(
        self,
        message: str,
        invalid_field: Optional[str] = None,
        valid_fields: Optional[list] = None,
    ):
        details = {}

        if invalid_field:
            details["invalid_field"] = invalid_field
        if valid_fields:
            details["valid_fields"] = valid_fields

        error_code = (
            ErrorCode.INVALID_SORT_FIELD if invalid_field else ErrorCode.INVALID_SORT_DIRECTION
        )

        super().__init__(message=message, error_code=error_code, status_code=400, details=details)


class FilterException(APIException):
    """Filter parameter errors."""

    def __init__(
        self,
        message: str,
        filter_name: str,
        invalid_value: Any,
        expected_type: Optional[str] = None,
    ):
        details = {"filter": filter_name, "invalid_value": str(invalid_value)}

        if expected_type:
            details["expected_type"] = expected_type

        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_FILTER,
            status_code=400,
            details=details,
        )


class PriceRangeException(APIException):
    """Price range validation errors."""

    def __init__(
        self,
        message: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ):
        details = {}

        if min_value is not None:
            details["pvp_min"] = min_value
        if max_value is not None:
            details["pvp_max"] = max_value

        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_PRICE_RANGE,
            status_code=400,
            details=details,
        )


# ==============================================================================
# Domain-Specific Business Errors
# ==============================================================================


class ProductNotFoundException(NotFoundException):
    """Product not found."""

    def __init__(self, codigo: str):
        super().__init__(message=f"Producto '{codigo}' no encontrado", resource_type="producto")
        self.details = {"codigo": codigo}


class InvalidProductException(APIException):
    """Invalid product data."""

    def __init__(self, message: str, product_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.PRODUCT_INVALID,
            status_code=422,
            details={"product_data": product_data} if product_data else None,
        )


class FamiliaNotFoundException(NotFoundException):
    """Familia not found."""

    def __init__(self, nombre: str):
        super().__init__(message=f"Familia '{nombre}' no encontrada", resource_type="familia")
        self.details = {"nombre": nombre}


class BC3DataException(APIException):
    """BC3 data validation errors."""

    def __init__(
        self,
        message: str,
        product_type: Optional[str] = None,
        missing_fields: Optional[list] = None,
    ):
        details = {}

        if product_type:
            details["bc3_product_type"] = product_type
        if missing_fields:
            details["missing_fields"] = missing_fields

        super().__init__(
            message=message,
            error_code=ErrorCode.BC3_DATA_INVALID,
            status_code=422,
            details=details,
        )


# ==============================================================================
# 5xx Server Errors
# ==============================================================================


class InternalServerException(APIException):
    """Internal Server Error (500)."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        details = None

        if original_exception:
            details = {
                "exception_type": type(original_exception).__name__,
                "exception_message": str(original_exception),
            }

        super().__init__(
            message=message,
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            details=details,
        )


class DatabaseException(APIException):
    """Database operation errors."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ):
        details = {}

        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        if original_exception:
            details["exception_type"] = type(original_exception).__name__
            details["exception_message"] = str(original_exception)

        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=500,
            details=details,
        )


class CacheException(APIException):
    """Cache operation errors."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        cache_key: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ):
        details = {}

        if operation:
            details["operation"] = operation
        if cache_key:
            details["cache_key"] = cache_key
        if original_exception:
            details["exception_type"] = type(original_exception).__name__
            details["exception_message"] = str(original_exception)

        super().__init__(
            message=message,
            error_code=ErrorCode.CACHE_ERROR,
            status_code=500,
            details=details,
        )


class CacheMissException(APIException):
    """Cache miss - treated as informational, not error."""

    def __init__(self, cache_key: str):
        super().__init__(
            message=f"Cache miss for key: {cache_key}",
            error_code=ErrorCode.CACHE_MISS,
            status_code=200,  # Not an error, just informational
            details={"cache_key": cache_key},
        )


class ServiceUnavailableException(APIException):
    """Service Unavailable (503)."""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message=message, error_code=ErrorCode.SERVICE_UNAVAILABLE, status_code=503)


# ==============================================================================
# Exception Factory Functions
# ==============================================================================


def create_validation_error(
    field: str,
    error_message: str,
    invalid_value: Any,
    valid_values: Optional[list] = None,
) -> ValidationException:
    """
    Create a validation exception with standardized format

    Args:
        field: Field name that failed validation
        error_message: Description of validation failure
        invalid_value: The invalid value provided
        valid_values: Optional list of valid values

    Returns:
        ValidationException with formatted details
    ."""
    validation_errors = {
        "field": field,
        "error": error_message,
        "invalid_value": str(invalid_value),
    }

    if valid_values:
        validation_errors["valid_values"] = valid_values

    return ValidationException(
        message=f"Validation failed for field '{field}': {error_message}",
        validation_errors={"errors": [validation_errors]},
    )


def wrap_exception(
    exception: Exception,
    custom_message: Optional[str] = None,
    error_code: Optional[ErrorCode] = None,
    context: Optional[Dict[str, Any]] = None,
) -> APIException:
    """
    Wrap a generic exception into an APIException

    Args:
        exception: The original exception
        custom_message: Optional custom error message
        error_code: Optional error code override
        context: Optional request context

    Returns:
        APIException with appropriate error information
    ."""
    message = custom_message or str(exception)
    error_code = error_code or ErrorCode.INTERNAL_ERROR

    # Determine status code based on exception type
    status_code = 500
    if isinstance(exception, (ValueError, KeyError, AttributeError)):
        status_code = 400
    elif isinstance(exception, PermissionError):
        status_code = 403
    elif isinstance(exception, FileNotFoundError):
        status_code = 404

    return APIException(
        message=message,
        error_code=error_code,
        status_code=status_code,
        details={"original_exception": type(exception).__name__},
        context=context,
    )
