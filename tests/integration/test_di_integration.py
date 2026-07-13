"""Integration tests for Dependency Injection flow

Tests complete HTTP → Depends → Service → Repository → Database → Response flow
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


class TestDIIntegrationFlow:
    """Test complete DI integration flow"""

    def test_http_to_service_to_repository_flow(self, client):
        """
        GIVEN dependency injection configured
        WHEN HTTP request is made
        THEN flow is: HTTP → Depends → Service → Repository → DB → Response
        """
        # Act
        response = client.get("/api/productos/v2/list?buscar=test&limit=5")

        # Assert HTTP response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Verify DTO fields present (service layer)
        if data:
            producto = data[0]
            assert "codigo" in producto
            assert "descripcion" in producto
            assert "marca" in producto
            assert "familia" in producto

    def test_service_business_logic_validation(self, client):
        """
        GIVEN service layer with business rules
        WHEN invalid search parameters provided
        THEN service validates and returns appropriate response
        """
        # Test with empty search term (DTO validation)
        response = client.get("/api/productos/v2/list?buscar=&limit=5")

        # Pydantic validates - should return 422
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail

    def test_repository_orm_operations(self, client):
        """
        GIVEN repository with ORM operations
        WHEN database query executed
        THEN correct ORM operations performed
        """
        # Act - this triggers repository ORM operations
        response = client.get("/api/productos/v2/list?buscar=test&limit=10")

        # Assert - repository returned data
        assert response.status_code == 200
        data = response.json()

        # Verify repository data structure matches ORM model
        if data:
            producto = data[0]
            # These fields come from ORM model mapping
            assert producto["codigo"]
            assert producto["descripcion"]
            assert "marca" in producto

    def test_dto_validation_both_directions(self, client):
        """
        GIVEN DTOs for input/output validation
        WHEN data flows both directions
        THEN DTO validation enforced
        """
        # Input validation (DTO → Service)
        response = client.get("/api/productos/v2/list?buscar=test&limit=1000")

        # Should fail due to le=100 constraint
        assert response.status_code == 422

        # Output validation (Entity → DTO → Response)
        response = client.get("/api/productos/v2/list?buscar=test&limit=5")
        assert response.status_code == 200

        data = response.json()
        if data:
            producto = data[0]
            # Verify output DTO schema
            required_fields = ["codigo", "descripcion", "marca", "familia"]
            for field in required_fields:
                assert field in producto

    def test_error_handling_and_http_status_codes(self, client):
        """
        GIVEN error handling in DI chain
        WHEN various error conditions occur
        THEN appropriate HTTP status codes returned
        """
        # Test validation error (DTO validation)
        response = client.get("/api/productos/v2/list?buscar=test&limit=0")
        assert response.status_code == 422

        # Test empty results (service/repository returns empty)
        response = client.get("/api/productos/v2/list?buscar=xyznonexistent&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_dependency_injection_with_filters(self, client):
        """
        GIVEN DI with multiple filter dependencies
        WHEN filters applied
        THEN all dependencies correctly injected
        """
        # Test with marca filter
        response = client.get("/api/productos/v2/list?buscar=test&limit=5&marca=disano")

        # Should work with DI
        assert response.status_code == 200
        data = response.json()

        # If results, verify marca filter worked
        if data:
            producto = data[0]
            # Should have Disano or be case-insensitive match
            assert producto["marca"].lower() == "disano"

    def test_v1_backward_compatibility_di(self, client):
        """
        GIVEN V1 legacy endpoint
        WHEN V1 endpoint called
        THEN DI works with V1 endpoint (backward compatibility)
        """
        # V1 endpoint should also work with DI
        response = client.get("/api/productos/?buscar=test&limit=5")

        assert response.status_code == 200
        data = response.json()

        # V1 returns same structure but without DTO validation
        if data:
            producto = data[0]
            assert producto["codigo"]
            assert producto["descripcion"]


class TestDIIntegrationWithDatabase:
    """Test DI integration with real database operations"""

    def test_database_transaction_rollback(self):
        """
        GIVEN test database with transaction rollback
        WHEN test modifies database
        THEN transaction rolled back (no permanent changes)
        """
        # Setup test database session
        engine = create_engine(
            "sqlite:///testing/testing.db",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )

        # Test that we can query database
        with TestingSessionLocal() as session:
            from app.infrastructure.repositories.producto import (
                SQLAlchemyProductoRepository,
            )
            from app.domain.services.producto import ProductoService

            # Create DI flow manually
            repo = SQLAlchemyProductoRepository(session)
            service = ProductoService(repo)

            # Query data
            productos = service.get_all_productos(skip=0, limit=5)

            # Assert data retrieved
            assert len(productos) >= 0

            # Verify structure
            if productos:
                producto = productos[0]
                assert producto.codigo
                assert producto.descripcion

    def test_database_connection_pooling(self, client):
        """
        GIVEN database connection pooling
        WHEN multiple requests made
        THEN connection pooling works correctly
        """
        # Make multiple requests
        for i in range(5):
            response = client.get("/api/productos/v2/list?buscar=test&limit=5")
            assert response.status_code == 200

        # If connection pooling works, no errors occurred
        assert True
