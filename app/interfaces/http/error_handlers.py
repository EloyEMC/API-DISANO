"""FastAPI exception handlers for API-DISANO V2 endpoints

Provides centralized error handling with standardized error responses
and proper HTTP status codes for different error types.
."""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError, HTTPException
from typing import Any, Optional
import logging
from fastapi.responses import JSONResponse

from app.interfaces.http.exceptions import (
    APIException,
    BadRequestException,
    NotFoundException,
    ValidationException,
    DatabaseException,
    CacheException,
    wrap_exception,
)


# Configure logging
logger = logging.getLogger(__name__)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    Handle custom API exceptions with standardized responses

    Args:
        request: FastAPI request object
        exc: Custom API exception

    Returns:
        JSONResponse with standardized error format
    ."""
    # Log the error
    logger.error(
        f"API Exception: {exc.error_code.value} - {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "query_params": dict(request.query_params),
            "error_code": exc.error_code.value,
            "status_code": exc.status_code,
            "details": exc.details,
        },
    )

    # Build error response
    error_response = {
        "error": exc.message,
        "error_code": exc.error_code.value,
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method,
        "timestamp": datetime_utc_now(),
    }

    # Add details if present
    if exc.details:
        error_response["details"] = exc.details

    # Add context if present
    if exc.context:
        error_response["context"] = exc.context

    # Add request information in development mode
    if is_development_mode():
        error_response["debug"] = {
            "query_params": dict(request.query_params),
            "path_params": dict(request.path_params),
            "request_id": getattr(request.state, "request_id", None),
        }

    return JSONResponse(status_code=exc.status_code, content=error_response)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTP exceptions

    Args:
        request: FastAPI request object
        exc: FastAPI HTTP exception

    Returns:
        JSONResponse with standardized error format
    ."""
    # Log the error
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        },
    )

    # Build error response
    error_response = {
        "error": exc.detail,
        "error_code": "HTTP_EXCEPTION",
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method,
        "timestamp": datetime_utc_now(),
    }

    return JSONResponse(status_code=exc.status_code, content=error_response)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors from FastAPI/Pydantic

    Args:
        request: FastAPI request object
        exc: Request validation exception

    Returns:
        JSONResponse with validation error details
    ."""
    # Log the validation error
    logger.warning(
        f"Validation Error: {len(exc.errors())} field(s) failed validation",
        extra={
            "path": request.url.path,
            "method": request.method,
            "validation_errors": exc.errors(),
        },
    )

    # Format validation errors
    formatted_errors = []
    for error in exc.errors():
        error_location = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append(
            {
                "field": error_location,
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input", None),
            }
        )

    # Build error response
    error_response = {
        "error": "Request validation failed",
        "error_code": "VALIDATION_ERROR",
        "status_code": 422,
        "path": request.url.path,
        "method": request.method,
        "timestamp": datetime_utc_now(),
        "details": {
            "validation_errors": formatted_errors,
            "error_count": len(formatted_errors),
        },
    }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_response
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other unexpected exceptions

    Args:
        request: FastAPI request object
        exc: Unexpected exception

    Returns:
        JSONResponse with internal server error
    ."""
    # Log the unexpected error
    logger.exception(
        f"Unexpected Exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        },
    )

    # Wrap in API exception for consistent handling
    wrapped_exc = wrap_exception(
        exc,
        custom_message="An unexpected error occurred",
        context={"path": request.url.path, "method": request.method},
    )

    # Build error response
    error_response = {
        "error": wrapped_exc.message,
        "error_code": wrapped_exc.error_code.value,
        "status_code": wrapped_exc.status_code,
        "path": request.url.path,
        "method": request.method,
        "timestamp": datetime_utc_now(),
    }

    # Add details
    if wrapped_exc.details:
        error_response["details"] = wrapped_exc.details

    # Add debug information in development mode
    if is_development_mode():
        error_response["debug"] = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "query_params": dict(request.query_params),
            "path_params": dict(request.path_params),
            "request_id": getattr(request.state, "request_id", None),
        }

    return JSONResponse(status_code=wrapped_exc.status_code, content=error_response)


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with FastAPI application

    Args:
        app: FastAPI application instance
    """
    # Register custom API exception handler
    app.add_exception_handler(APIException, api_exception_handler)

    # Register FastAPI HTTP exception handler
    app.add_exception_handler(HTTPException, http_exception_handler)

    # Register request validation exception handler
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Register generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)


# ==============================================================================
# Helper Functions
# ==============================================================================


def datetime_utc_now():
    """Get current UTC datetime as ISO string."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def is_development_mode() -> bool:
    """
    Check if application is running in development mode

    Returns:
        True if development mode, False otherwise
    ."""
    import os

    return os.getenv("ENVIRONMENT", "development").lower() == "development"


def create_error_response(
    message: str,
    error_code: str,
    status_code: int,
    details: Optional[dict[str, Any]] = None,
    debug_info: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Create a standardized error response dictionary

    Args:
        message: Error message
        error_code: Standardized error code
        status_code: HTTP status code
        details: Optional error details
        debug_info: Optional debug information (development only)

    Returns:
        Standardized error response dictionary
    ."""
    response = {
        "error": message,
        "error_code": error_code,
        "status_code": status_code,
        "timestamp": datetime_utc_now(),
    }

    if details:
        response["details"] = details

    if debug_info and is_development_mode():
        response["debug"] = debug_info

    return response


def log_error(
    logger_instance: logging.Logger,
    error: Exception,
    request: Request,
    additional_context: Optional[dict[str, Any]] = None,
) -> None:
    """
    Log an error with standardized format

    Args:
        logger_instance: Logger instance to use
        error: Exception that occurred
        request: FastAPI request object
        additional_context: Optional additional context
    ."""
    context = {
        "path": request.url.path,
        "method": request.method,
        "query_params": dict(request.query_params),
        "path_params": dict(request.path_params),
        "client_host": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", None),
    }

    if additional_context:
        context.update(additional_context)

    # Extract error type and message
    error_type = type(error).__name__
    error_message = str(error)

    # Log with appropriate level
    if isinstance(error, (BadRequestException, ValidationException)):
        logger_instance.warning(f"{error_type}: {error_message}", extra=context)
    elif isinstance(error, (NotFoundException,)):
        logger_instance.info(f"{error_type}: {error_message}", extra=context)
    elif isinstance(error, (DatabaseException, CacheException)):
        logger_instance.error(f"{error_type}: {error_message}", extra=context)
    else:
        logger_instance.exception(f"{error_type}: {error_message}", extra=context)
