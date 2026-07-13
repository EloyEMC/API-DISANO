"""Integration tests for ProductoModel

Tests SQLAlchemy model operations with actual database.
"""

import pytest

from app.infrastructure.models.producto_clean import ProductoModelClean
from app.infrastructure.database.connection import get_db_session


class TestProductoModelClean:
    """Tests for ProductoModelClean SQLAlchemy operations"""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup database connection for tests"""
        # Using existing testing database
        # productos_clean view already exists
        yield
        # Cleanup handled by session context manager

    def test_model_query_existing_product(self):
        """Test querying existing product from testing.db"""
        with get_db_session() as session:
            # Query for a product that should exist
            model = (
                session.query(ProductoModelClean)
                .filter(ProductoModelClean.marca != "")
                .first()
            )

            assert model is not None
            assert hasattr(model, "codigo")
            assert hasattr(model, "descripcion")
            assert hasattr(model, "marca")

    def test_model_to_entity_conversion(self):
        """Test converting model to domain entity"""
        with get_db_session() as session:
            model = (
                session.query(ProductoModelClean)
                .filter(ProductoModelClean.marca != "")
                .first()
            )

            if not model:
                pytest.skip("No products found in database")

            entity = model.to_entity()

            assert entity is not None
            assert entity.codigo == model.codigo
            assert entity.descripcion == model.descripcion
            assert entity.marca == model.marca

    def test_model_from_entity_conversion(self):
        """Test creating model from domain entity"""
        from app.domain.entities.producto import ProductoEntity

        entity = ProductoEntity(
            codigo="TEST001",
            descripcion="Test Product",
            marca="TestBrand",
            pvp=99.99,
        )

        model = ProductoModelClean.from_entity(entity)

        assert model.codigo == "TEST001"
        assert model.descripcion == "Test Product"
        assert model.marca == "TestBrand"
        assert model.pvp == 99.99

    def test_model_repr(self):
        """Test model string representation"""
        model = ProductoModelClean(
            codigo="TEST001",
            descripcion="A very long description that should be truncated",
            marca="Test",
        )

        repr_str = repr(model)

        assert "TEST001" in repr_str
        assert "A very long descript" in repr_str
