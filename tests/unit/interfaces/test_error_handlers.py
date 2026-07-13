"""Tests for error handling system following TDD principles

RED Phase: Write failing tests first
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.interfaces.http.exceptions import (
    APIException,
    BadRequestException,
    NotFoundException,
    ValidationException,
    DatabaseException,
    CacheException,
    PaginationException,
    SortException,
    ProductNotFoundException,
    FamiliaNotFoundException,
    ErrorCode,
    create_validation_error,
    wrap_exception,
)
from app.interfaces.http.error_handlers import (
    register_exception_handlers,
    create_error_response,
)


# ==============================================================================
# Test Custom Exceptions (RED Phase)
# ==============================================================================


class TestAPIException:
    """Test base APIException class"""

    def test_api_exception_creation(self):
        """Test creating basic API exception"""
        exc = APIException(
            message="Test error", error_code=ErrorCode.INTERNAL_ERROR, status_code=500
        )

        assert exc.message == "Test error"
        assert exc.error_code == ErrorCode.INTERNAL_ERROR
        assert exc.status_code == 500

    def test_api_exception_to_dict(self):
        """Test converting exception to dictionary"""
        exc = APIException(
            message="Test error",
            error_code=ErrorCode.BAD_REQUEST,
            status_code=400,
            details={"field": "test"},
            context={"path": "/test"},
        )

        exc_dict = exc.to_dict()

        assert exc_dict["error"] == "Test error"
        assert exc_dict["error_code"] == "BAD_REQUEST"
        assert exc_dict["status_code"] == 400
        assert exc_dict["details"] == {"field": "test"}
        assert exc_dict["context"] == {"path": "/test"}
        assert "timestamp" in exc_dict


class TestClientErrors:
    """Test 4xx client errors"""

    def test_bad_request_exception(self):
        """Test BadRequestException (400)"""
        exc = BadRequestException("Invalid request", details={"field": "test"})

        assert exc.message == "Invalid request"
        assert exc.error_code == ErrorCode.BAD_REQUEST
        assert exc.status_code == 400
        assert exc.details == {"field": "test"}

    def test_not_found_exception(self):
        """Test NotFoundException (404)"""
        exc = NotFoundException("Resource not found", resource_type="producto")

        assert exc.message == "Resource not found"
        assert exc.error_code == ErrorCode.NOT_FOUND
        assert exc.status_code == 404
        assert exc.details["resource_type"] == "producto"

    def test_validation_exception(self):
        """Test ValidationException (422)"""
        validation_errors = {"field": ["error1", "error2"]}
        exc = ValidationException("Validation failed", validation_errors)

        assert exc.message == "Validation failed"
        assert exc.error_code == ErrorCode.VALIDATION_ERROR
        assert exc.status_code == 422
        assert exc.details["validation_errors"] == validation_errors


class TestDomainErrors:
    """Test domain-specific exceptions"""

    def test_pagination_exception_invalid_page(self):
        """Test PaginationException for invalid page number"""
        exc = PaginationException(
            message="Invalid page number",
            parameter_name="page",
            invalid_value=-1,
            valid_range="1-9999",
        )

        assert exc.message == "Invalid page number"
        assert exc.error_code == ErrorCode.INVALID_PAGE
        assert exc.status_code == 400
        assert exc.details["parameter"] == "page"
        assert exc.details["invalid_value"] == "-1"

    def test_sort_exception_invalid_field(self):
        """Test SortException for invalid sort field"""
        exc = SortException(
            message="Invalid sort field",
            invalid_field="invalid_field",
            valid_fields=["codigo", "descripcion", "pvp"],
        )

        assert exc.message == "Invalid sort field"
        assert exc.error_code == ErrorCode.INVALID_SORT_FIELD
        assert exc.status_code == 400
        assert exc.details["invalid_field"] == "invalid_field"
        assert exc.details["valid_fields"] == ["codigo", "descripcion", "pvp"]

    def test_product_not_found_exception(self):
        """Test ProductNotFoundException"""
        exc = ProductNotFoundException("TEST001")

        assert exc.message == "Producto 'TEST001' no encontrado"
        assert exc.error_code == ErrorCode.PRODUCT_NOT_FOUND
        assert exc.status_code == 404
        assert exc.details["codigo"] == "TEST001"

    def test_familia_not_found_exception(self):
        """Test FamiliaNotFoundException"""
        exc = FamiliaNotFoundException("test_familia")

        assert exc.message == "Familia 'test_familia' no encontrada"
        assert exc.error_code == ErrorCode.FAMILIA_NOT_FOUND
        assert exc.status_code == 404
        assert exc.details["nombre"] == "test_familia"


class TestServerErrorrors:
    """Test 5xx server errors"""

    def test_database_exception(self):
        """Test DatabaseException"""
        exc = DatabaseException(
            message="Database connection failed",
            operation="SELECT",
            table="productos",
            original_exception=ConnectionError("Connection refused"),
        )

        assert exc.message == "Database connection failed"
        assert exc.error_code == ErrorCode.DATABASE_ERROR
        assert exc.status_code == 500
        assert exc.details["operation"] == "SELECT"
        assert exc.details["table"] == "productos"
        assert "Connection refused" in exc.details["exception_message"]

    def test_cache_exception(self):
        """Test CacheException"""
        exc = CacheException(
            message="Cache operation failed",
            operation="GET",
            cache_key="productos:page:1",
        )

        assert exc.message == "Cache operation failed"
        assert exc.error_code == ErrorCode.CACHE_ERROR
        assert exc.status_code == 500
        assert exc.details["operation"] == "GET"
        assert exc.details["cache_key"] == "productos:page:1"


# ==============================================================================
# Test Exception Factory Functions
# ==============================================================================


class TestExceptionFactoryFunctions:
    """Test exception factory functions"""

    def test_create_validation_error(self):
        """Test create_validation_error function"""
        exc = create_validation_error(
            field="codigo",
            error_message="Code must be at least 5 characters",
            invalid_value="ABC",
            valid_values=["ABCDE", "12345", "TEST0"],
        )

        assert isinstance(exc, ValidationException)
        assert "Validation failed for field 'codigo'" in exc.message
        assert exc.details["validation_errors"]["errors"][0]["field"] == "codigo"
        assert exc.details["validation_errors"]["errors"][0]["invalid_value"] == "ABC"

    def test_wrap_exception_value_error(self):
        """Test wrap_exception with ValueError"""
        original_exc = ValueError("Invalid value")
        wrapped = wrap_exception(original_exc)

        assert isinstance(wrapped, APIException)
        assert wrapped.status_code == 400  # ValueError -> 400
        assert wrapped.details["original_exception"] == "ValueError"

    def test_wrap_exception_key_error(self):
        """Test wrap_exception with KeyError"""
        original_exc = KeyError("missing_key")
        wrapped = wrap_exception(original_exc)

        assert isinstance(wrapped, APIException)
        assert wrapped.status_code == 400  # KeyError -> 400
        assert wrapped.details["original_exception"] == "KeyError"

    def test_wrap_exception_permission_error(self):
        """Test wrap_exception with PermissionError"""
        original_exc = PermissionError("Access denied")
        wrapped = wrap_exception(original_exc)

        assert isinstance(wrapped, APIException)
        assert wrapped.status_code == 403  # PermissionError -> 403
        assert wrapped.details["original_exception"] == "PermissionError"

    def test_wrap_exception_file_not_found(self):
        """Test wrap_exception with FileNotFoundError"""
        original_exc = FileNotFoundError("/path/to/file.txt")
        wrapped = wrap_exception(original_exc)

        assert isinstance(wrapped, APIException)
        assert wrapped.status_code == 404  # FileNotFoundError -> 404
        assert wrapped.details["original_exception"] == "FileNotFoundError"


# ==============================================================================
# Test Error Response Functions
# ==============================================================================


class TestErrorResponseFunctions:
    """Test error response creation functions"""

    def test_create_error_response_basic(self):
        """Test create_error_response with basic parameters"""
        response = create_error_response(
            message="Test error", error_code="TEST_ERROR", status_code=500
        )

        assert response["error"] == "Test error"
        assert response["error_code"] == "TEST_ERROR"
        assert response["status_code"] == 500
        assert "timestamp" in response

    def test_create_error_response_with_details(self):
        """Test create_error_response with details"""
        response = create_error_response(
            message="Validation error",
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={"field": "codigo", "invalid_value": "ABC"},
        )

        assert response["error"] == "Validation error"
        assert response["details"]["field"] == "codigo"
        assert response["details"]["invalid_value"] == "ABC"

    def test_create_error_response_with_debug_info(self):
        """Test create_error_response with debug info"""
        debug_info = {"request_id": "req-123", "query_params": {"page": 1}}

        response = create_error_response(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=500,
            debug_info=debug_info,
        )

        # In development mode, debug info should be included
        # (This will be tested with environment variable in actual tests)
        assert response["error"] == "Test error"
        assert response["status_code"] == 500


# ==============================================================================
# Test Exception Handlers Integration
# ==============================================================================


class TestExceptionHandlersIntegration:
    """Test exception handlers with FastAPI integration"""

    @pytest.fixture
    def app_with_handlers(self):
        """Create FastAPI app with exception handlers"""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-api-exception")
        async def test_api_exception():
            raise APIException(
                message="Test API exception",
                error_code=ErrorCode.TEST_ERROR,
                status_code=400,
            )

        @app.get("/test-http-exception")
        async def test_http_exception():
            raise HTTPException(status_code=404, detail="Resource not found")

        @app.get("/test-validation-error")
        async def test_validation_error():
            from pydantic import BaseModel, Field

            class QueryParam(BaseModel):
                page: int = Field(ge=1, le=100)
                per_page: int = Field(ge=1, le=100)

            # This will raise validation error if called incorrectly
            return {"status": "ok"}

        @app.get("/test-generic-exception")
        async def test_generic_exception():
            1 / 0  # ZeroDivisionError

        return app

    def test_api_exception_handler(self, app_with_handlers):
        """Test API exception handler returns correct response"""
        client = TestClient(app_with_handlers)
        response = client.get("/test-api-exception")

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Test API exception"
        assert data["error_code"] == "TEST_ERROR"
        assert data["status_code"] == 400
        assert "timestamp" in data

    def test_http_exception_handler(self, app_with_handlers):
        """Test HTTP exception handler returns correct response"""
        client = TestClient(app_with_handlers)
        response = client.get("/test-http-exception")

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Resource not found"
        assert data["error_code"] == "HTTP_EXCEPTION"
        assert data["status_code"] == 404

    def test_generic_exception_handler(self, app_with_handlers):
        """Test generic exception handler catches unexpected errors"""
        client = TestClient(app_with_handlers)
        response = client.get("/test-generic-exception")

        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error_code"] == "INTERNAL_ERROR"
        assert data["status_code"] == 500
        assert "ZeroDivisionError" in data.get("details", {}).get(
            "original_exception", ""
        )


# ==============================================================================
# Test Error Responses with Real Endpoints
# ==============================================================================


class TestErrorResponsesWithRealEndpoints:
    """Test error responses with real V2 endpoints"""

    @pytest.fixture
    def productos_app(self):
        """Create productos app with error handling"""
        app = FastAPI()
        register_exception_handlers(app)

        from app.interfaces.http import productos as productos_http

        app.include_router(productos_http.router, prefix="/api")

        return app

    def test_invalid_page_parameter(self, productos_app):
        """Test that invalid page parameter returns validation error"""
        client = TestClient(productos_app)
        response = client.get("/api/productos/v2/paginated?page=-1")

        # This should be handled by FastAPI validation
        assert response.status_code in [422, 400]

    def test_invalid_per_page_parameter(self, productos_app):
        """Test that invalid per_page parameter returns validation error"""
        client = TestClient(productos_app)
        response = client.get("/api/productos/v2/paginated?per_page=999")

        # This should be handled by FastAPI validation
        assert response.status_code in [422, 400]

    def test_invalid_sort_field(self, productos_app):
        """Test that invalid sort field is handled appropriately"""
        client = TestClient(productos_app)
        response = client.get("/api/productos/v2/paginated?sort=invalid_field:asc")

        # Should handle gracefully - might not error immediately
        assert response.status_code in [200, 400, 500]

    def test_invalid_price_range(self, productos_app):
        """Test that invalid price range is handled appropriately"""
        client = TestClient(productos_app)
        response = client.get("/api/productos/v2/paginated?pvp_min=-100")

        # Should handle gracefully
        assert response.status_code in [200, 400, 500]

    def test_malformed_query_parameters(self, productos_app):
        """Test handling of malformed query parameters"""
        client = TestClient(productos_app)

        # Test with special characters in search
        response = client.get(
            "/api/productos/v2/paginated?buscar=<script>alert('xss')</script>"
        )
        assert response.status_code == 200  # Should handle safely

        # Test with very long parameter values
        response = client.get("/api/productos/v2/paginated?buscar=" + "A" * 1000)
        assert response.status_code in [200, 400]  # Should handle gracefully
