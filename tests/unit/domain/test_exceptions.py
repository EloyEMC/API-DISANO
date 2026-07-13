"""Unit tests for Domain Exceptions

Tests validation and not found exceptions.
"""

from app.domain.exceptions.not_found import (
    ValidationException,
    ProductoYaExisteException,
    ProductoNotFoundException,
)


class TestValidationException:
    """Tests for ValidationException"""

    def test_creation_with_field_and_message(self):
        """Test creating exception with field and message"""
        exception = ValidationException("codigo", "Código inválido")

        assert exception.field == "codigo"
        assert exception.message == "Código inválido"
        assert "codigo" in str(exception)
        assert "Código inválido" in str(exception)

    def test_str_representation(self):
        """Test string representation"""
        exception = ValidationException("descripcion", "Mínimo 2 caracteres")

        expected = "Validation error on descripcion: Mínimo 2 caracteres"
        assert str(exception) == expected


class TestProductoNotFoundException:
    """Tests for ProductoNotFoundException"""

    def test_creation_with_codigo(self):
        """Test creating exception with product code"""
        exception = ProductoNotFoundException("TEST001")

        assert exception.codigo == "TEST001"
        assert "TEST001" in str(exception)
        assert "no encontrado" in str(exception).lower()

    def test_custom_message(self):
        """Test creating exception with custom message"""
        exception = ProductoNotFoundException("TEST002", "Producto eliminado: TEST002")

        assert exception.codigo == "TEST002"
        assert "Producto eliminado" in str(exception)


class TestProductoYaExisteException:
    """Tests for ProductoYaExisteException"""

    def test_creation(self):
        """Test creating exception"""
        exception = ProductoYaExisteException("TEST001")

        assert exception.codigo == "TEST001"
        assert exception.field == "codigo"
        # Exception message includes field and message but not necessarily codigo
        assert "validation error" in str(exception).lower()

    def test_default_message(self):
        """Test default message is used"""
        exception = ProductoYaExisteException("TEST001")

        assert "ya existe" in str(exception).lower()
        assert "código" in str(exception).lower()

    def test_custom_message(self):
        """Test custom message"""
        exception = ProductoYaExisteException(
            "TEST001", "Código duplicado en importación"
        )

        assert "Código duplicado en importación" in str(exception)
