"""Unit tests for ProductoEntity

Tests domain entity validation and behavior.
."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.domain.entities.producto import ProductoEntity


class TestProductoEntity:
    """Tests for ProductoEntity validation and behavior."""

    def test_create_producto_minimal_required(self):
        """Test creating product with minimal required fields."""
        producto = ProductoEntity(codigo="TEST001", descripcion="Test Product", marca="Test")

        assert producto.codigo == "TEST001"
        assert producto.descripcion == "Test Product"
        assert producto.marca == "Test"

    def test_create_producto_with_optional_fields(self):
        """Test creating product with all fields."""
        now = datetime.now()
        producto = ProductoEntity(
            codigo="TEST002",
            descripcion="Test Product Full",
            marca="TestBrand",
            familia="TestFamily",
            pvp=99.99,
            bc3_descripcion_corta="Short desc",
            bc3_product_type="test_type",
            bc3_descripcion_completa="Full BC3 desc",
            created_at=now,
            updated_at=now,
        )

        assert producto.codigo == "TEST002"
        assert producto.familia == "TestFamily"
        assert producto.pvp == 99.99
        assert producto.bc3_descripcion_corta == "Short desc"

    def test_producto_codigo_required(self):
        """Test that codigo is required."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoEntity(descripcion="Test", marca="Test")

        assert "codigo" in str(exc_info.value)

    def test_producto_descripcion_min_length(self):
        """Test that descripcion must have min length 2."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoEntity(codigo="TEST", descripcion="A", marca="Test")

        assert "descripcion" in str(exc_info.value)

    def test_producto_marca_required(self):
        """Test that marca is required."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoEntity(codigo="TEST", descripcion="Test Product")

        assert "marca" in str(exc_info.value)

    def test_producto_pvp_negative_rejected(self):
        """Test that negative pvp is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProductoEntity(codigo="TEST", descripcion="Test", marca="Test", pvp=-10.0)

        assert "pvp" in str(exc_info.value) or "price" in str(exc_info.value).lower()

    def test_producto_pvp_zero_allowed(self):
        """Test that pvp=0 is allowed."""
        producto = ProductoEntity(codigo="TEST", descripcion="Test", marca="Test", pvp=0)
        assert producto.pvp == 0

    def test_producto_entity_is_immutable(self):
        """Test that ProductoEntity is immutable (frozen)."""
        producto = ProductoEntity(codigo="TEST", descripcion="Test", marca="Test")

        with pytest.raises(Exception):  # FrozenInstanceError
            producto.descripcion = "Updated"

    def test_producto_entity_serialization(self):
        """Test that entity can be serialized to dict."""
        producto = ProductoEntity(codigo="TEST", descripcion="Test", marca="Test")

        data = producto.model_dump()

        assert data["codigo"] == "TEST"
        assert data["descripcion"] == "Test"
        assert data["marca"] == "Test"

    def test_producto_entity_from_dict(self):
        """Test creating entity from dictionary."""
        data = {
            "codigo": "TEST",
            "descripcion": "Test",
            "marca": "TestBrand",
            "familia": "TestFamily",
            "pvp": 99.99,
        }

        producto = ProductoEntity(**data)

        assert producto.codigo == "TEST"
        assert producto.familia == "TestFamily"
        assert producto.pvp == 99.99
