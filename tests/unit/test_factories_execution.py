"""
Tests Unitarios - Models Execution (TDD + AAA + Factories)
============================================================

Tests que ejecutan código real usando factories BC3-Suite.
AAA pattern: Arrange, Act, Assert.
"""

import pytest
from tests.factories.factories import (
    ProductoFactory,
    UserFactory,
    OTPFactory,
    RequestFactory,
)


class TestProductoFactoryExecution:
    """Tests que ejecutan Producto Factory BC3-Suite (TDD)."""

    def test_producto_factory_base_creates_valid_instance(self):
        """
        AAA: Arrange (factory), Act (base()), Assert (validation)
        """
        # Arrange - Usar factory
        producto_dict = ProductoFactory.base()

        # Act - No hay acción, la factory ya creó el objeto

        # Assert - Verificar estructura
        assert "codigo" in producto_dict
        assert "descripcion" in producto_dict
        assert "marca" in producto_dict
        assert "pvp" in producto_dict

    def test_producto_factory_with_bc3(self):
        """GREEN: Crear producto con campos BC3."""
        # Arrange - Usar factory con BC3
        producto = ProductoFactory.with_bc3()

        # Act - No hay acción, la factory ya creó el objeto

        # Assert - Verificar campos BC3
        bc3_fields = [
            "bc3_descripcion_corta",
            "bc3_descripcion_larga",
            "bc3_product_type",
            "bc3_descripcion_completa",
            "bc3_processed_at",
        ]
        for field in bc3_fields:
            assert field in producto

    def test_producto_factory_create_batch(self):
        """GREEN: Crear múltiples productos con factory."""
        # Arrange
        batch_size = 3

        # Act
        productos = ProductoFactory.create_batch(batch_size)

        # Assert
        assert len(productos) == batch_size
        for producto in productos:
            assert "codigo" in producto
            assert "descripcion" in producto

    def test_producto_factory_mandatory_fields(self):
        """GREEN: Verificar campos obligatorios."""
        # Arrange - Usar factory
        producto = ProductoFactory.base()

        # Assert - Campos obligatorios existentes
        mandatory_fields = ["codigo", "descripcion", "pvp"]
        for field in mandatory_fields:
            assert field in producto
            assert producto[field] is not None


class TestOTPFactoryExecution:
    """Tests que ejecutan OTP Factory BC3-Suite (TDD)."""

    def test_otp_factory_creates_valid_otp(self):
        """GREEN: Crear OTP válido con factory."""
        # Arrange
        otp_dict = OTPFactory.valid()

        # Act - No hay acción, la factory ya creó el objeto

        # Assert
        assert otp_dict["code"] is not None
        assert isinstance(otp_dict["code"], str)
        assert len(otp_dict["code"]) == 6

    def test_otp_factory_expired(self):
        """GREEN: Crear OTP expirado con factory."""
        # Arrange
        otp_dict = OTPFactory.expired()

        # Act - No hay acción, la factory ya creó el objeto

        # Assert
        assert otp_dict["code"] is not None
        assert otp_dict["verified"] == False


class TestUserFactoryExecution:
    """Tests que ejecutan User Factory BC3-Suite (TDD)."""

    def test_user_factory_creates_admin(self):
        """GREEN: Crear usuario admin con factory."""
        # Arrange
        user_dict = UserFactory.admin()

        # Assert
        assert user_dict["role"] == "admin"
        assert "email" in user_dict

    def test_user_factory_creates_sales(self):
        """GREEN: Crear usuario sales con factory."""
        # Arrange
        user_dict = UserFactory.sales()

        # Assert
        assert user_dict["role"] == "sales"
        assert "email" in user_dict

    def test_user_factory_creates_coordinator(self):
        """GREEN: Crear usuario coordinator con factory."""
        # Arrange
        user_dict = UserFactory.coordinator()

        # Assert
        assert user_dict["rol_en_zona"] == "coordinador"
        assert "zona_id" in user_dict


class TestRequestFactoryExecution:
    """Tests que ejecutan Request Factory BC3-Suite (TDD)."""

    def test_request_factory_get_producto(self):
        """GREEN: Crear request GET para producto."""
        # Arrange
        request_dict = RequestFactory.create_producto_get_request()

        # Assert
        assert request_dict["method"] == "GET"
        assert "/productos" in request_dict["path"]
        assert request_dict["params"] is not None

    def test_request_factory_admin_create(self):
        """GREEN: Crear request POST para admin."""
        # Arrange
        request_dict = RequestFactory.create_admin_create_request()

        # Assert
        assert request_dict["method"] == "POST"
        assert request_dict["path"] == "/api/admin/productos"
        assert request_dict["body"] is not None


if __name__ == "__main__":
    pytest.main([__file__])
