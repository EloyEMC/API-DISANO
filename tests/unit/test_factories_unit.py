"""
Tests Unitarios - Factories (Sin Client Fixture)
===============================================

Tests unitarios de factories que NO usan client fixture.
."""

import pytest
from tests.factories.factories import ProductoFactory, OTPFactory, UserFactory


class TestProductoFactory:
    """Tests de ProductoFactory."""

    def test_producto_base_creates_valid_structure(self):
        ."""Crear producto base con estructura válida."""
        producto = ProductoFactory.base()

        assert "codigo" in producto
        assert "descripcion" in producto
        assert "pvp" in producto
        assert "marca" in producto
        assert "familia_web" in producto
        assert "descontinuado" in producto

    def test_producto_bc3_creates_complete_structure(self):
        """Crear producto con campos BC3 llenos."""
        producto = ProductoFactory.with_bc3()

        assert "bc3_descripcion_corta" in producto
        assert "bc3_descripcion_larga" in producto
        assert "bc3_product_type" in producto
        assert "bc3_descripcion_completa" in producto
        assert "bc3_processed_at" in producto

    def test_producto_create_batch_creates_multiple(self):
        """Crear múltiples productos."""
        productos = ProductoFactory.create_batch(count=5)

        assert len(productos) == 5
        assert all("codigo" in p for p in productos)

    def test_producto_descontinuado_flag(self):
        """Crear producto descontinuado."""
        producto = ProductoFactory.descontinuado()

        assert producto["descontinuado"] is True


class TestOTPFactory:
    """Tests de OTPFactory."""

    def test_otp_valid_creates_complete_structure(self):
        ."""Crear OTP válido con estructura completa."""
        otp_data = OTPFactory.valid()

        assert "code" in otp_data
        assert "email" in otp_data
        assert "expiry" in otp_data
        assert "attempts" in otp_data
        assert "verified" in otp_data

    def test_otp_code_is_valid_format(self):
        """OTP tiene formato válido."""
        otp_data = OTPFactory.valid()

        assert len(otp_data["code"]) == 6
        assert otp_data["code"].isdigit()

    def test_otp_expired_has_past_expiry(self):
        """OTP expirado tiene expiry en pasado."""
        from datetime import datetime

        otp_data = OTPFactory.expired()

        assert otp_data["expiry"] < datetime.now()

    def test_otp_max_attempts_reached(self):
        """OTP con máximo de intentos."""
        otp_data = OTPFactory.max_attempts_reached()

        assert otp_data["attempts"] == 3


class TestUserFactory:
    """Tests de UserFactory."""

    def test_admin_user_creates_correct_role(self):
        ."""Crear usuario admin."""
        user = UserFactory.admin()

        assert user["role"] == "admin"

    def test_sales_user_creates_correct_role(self):
        """Crear usuario sales."""
        user = UserFactory.sales()

        assert user["role"] == "sales"

    def test_coordinator_user_creates_correct_role(self):
        """Crear usuario coordinador."""
        user = UserFactory.coordinator()

        assert user["role"] == "sales"
        assert user["rol_en_zona"] == "coordinador"
        assert "zona_id" in user


if __name__ == "__main__":
    pytest.main([__file__])
