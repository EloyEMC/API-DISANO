"""Unit tests for ProductoService

Tests business logic and validation rules.
."""

from datetime import datetime
from unittest.mock import Mock
from pydantic_core import ValidationError

import pytest

from app.domain.entities.producto import ProductoEntity
from app.domain.exceptions.not_found import (
    ProductoNotFoundException,
    ProductoYaExisteException,
)
from app.domain.repositories.producto import ProductoRepositoryInterface
from app.domain.services.producto import ProductoService
from app.application.dto.producto import (
    ProductoCreateDTO,
    ProductoUpdateDTO,
    ProductoSearchDTO,
)


class TestProductoService:
    """Tests for ProductoService business logic."""

    def test_crear_producto_success(self):
        """Test creating product successfully."""
        # Arrange
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.get_by_codigo.side_effect = ProductoNotFoundException("TEST001")
        mock_repo.save.return_value = ProductoEntity(
            codigo="TEST001",
            descripcion="Test Product",
            marca="TestBrand",
            pvp=99.99,
            created_at=None,
            updated_at=None,
        )

        service = ProductoService(mock_repo)
        dto = ProductoCreateDTO(
            codigo="TEST001",
            descripcion="Test Product",
            marca="TestBrand",
            pvp=99.99,
        )

        # Act
        result = service.crear_producto(dto)

        # Assert
        assert result.codigo == "TEST001"
        assert result.descripcion == "Test Product"
        mock_repo.save.assert_called_once()

    def test_crear_producto_duplicate_code(self):
        """Test creating product with duplicate code raises error."""
        # Arrange
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.get_by_codigo.return_value = ProductoEntity(
            codigo="TEST001",
            descripcion="Existing",
            marca="Test",
            created_at=None,
            updated_at=None,
        )

        service = ProductoService(mock_repo)
        dto = ProductoCreateDTO(
            codigo="TEST001",
            descripcion="Test Product",
            marca="Test",
        )

        # Act & Assert
        with pytest.raises(ProductoYaExisteException):
            service.crear_producto(dto)

        def test_crear_producto_validacion_descripcion_corta(self):
            """Test creating product with short description raises error."""
            # Arrange
            mock_repo = Mock(spec=ProductoRepositoryInterface)
            mock_repo.get_by_codigo.side_effect = ProductoNotFoundException("TEST001")

            service = ProductoService(mock_repo)

            # Act & Assert - ValidationError occurs at DTO creation
            with pytest.raises(ValidationError):
                dto = ProductoCreateDTO(
                    codigo="TEST001",
                    descripcion="A",  # Too short - Pydantic validates
                    marca="Test",
                )
                service.crear_producto(dto)

        def test_crear_producto_validacion_pvp_negativo(self):
            """Test creating product with negative price raises error."""
            # Arrange
            mock_repo = Mock(spec=ProductoRepositoryInterface)
            mock_repo.get_by_codigo.side_effect = ProductoNotFoundException("TEST001")

            service = ProductoService(mock_repo)

            # Act & Assert - ValidationError occurs at DTO creation
            with pytest.raises(ValidationError):
                dto = ProductoCreateDTO(
                    codigo="TEST001",
                    descripcion="Test Product",
                    marca="Test",
                    pvp=-10.0,  # Negative - Pydantic validates
                )
                service.crear_producto(dto)

    def test_actualizar_producto_success(self):
        """Test updating existing product."""
        # Arrange
        existing = ProductoEntity(
            codigo="TEST001",
            descripcion="Old Description",
            marca="TestBrand",
            pvp=50.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.get_by_codigo.return_value = existing
        mock_repo.save.return_value = ProductoEntity(
            codigo="TEST001",
            descripcion="New Description",
            marca="TestBrand",
            pvp=99.99,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
        )

        service = ProductoService(mock_repo)
        dto = ProductoUpdateDTO(
            descripcion="New Description",
            pvp=99.99,
        )

        # Act
        result = service.actualizar_producto("TEST001", dto)

        # Assert
        assert result.descripcion == "New Description"
        assert result.pvp == 99.99
        mock_repo.save.assert_called_once()

    def test_actualizar_producto_not_found(self):
        """Test updating non-existent product raises error."""
        # Arrange
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.get_by_codigo.side_effect = ProductoNotFoundException("TEST001")

        service = ProductoService(mock_repo)
        dto = ProductoUpdateDTO(descripcion="New Description")

        # Act & Assert
        with pytest.raises(ProductoNotFoundException):
            service.actualizar_producto("TEST001", dto)

    def test_actualizar_producto_pvp_negativo(self):
        """Test updating product with negative price raises error."""
        # Arrange
        existing = ProductoEntity(
            codigo="TEST001",
            descripcion="Old Description",
            marca="TestBrand",
            familia=None,
            pvp=50.0,
            bc3_descripcion_corta=None,
            bc3_product_type=None,
            bc3_descripcion_completa=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.get_by_codigo.return_value = existing

        service = ProductoService(mock_repo)

        # Act & Assert - ValidationError occurs at DTO creation
        with pytest.raises(ValidationError):
            dto = ProductoUpdateDTO(pvp=-10.0)  # Negative - Pydantic validates
            service.actualizar_producto("TEST001", dto)

    def test_buscar_productos(self):
        """Test searching products."""
        # Arrange
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_results = [
            ProductoEntity(
                codigo="TEST001",
                descripcion="Test Product 1",
                marca="Test",
                pvp=99.99,
                created_at=None,
                updated_at=None,
            ),
            ProductoEntity(
                codigo="TEST002",
                descripcion="Test Product 2",
                marca="Test",
                pvp=199.99,
                created_at=None,
                updated_at=None,
            ),
        ]
        mock_repo.buscar_productos.return_value = mock_results

        service = ProductoService(mock_repo)
        dto = ProductoSearchDTO(buscar="Test", limit=10)

        # Act
        result = service.buscar_productos(dto)

        # Assert
        assert len(result) == 2
        mock_repo.buscar_productos.assert_called_once()

    def test_obtener_producto(self):
        """Test getting product by code."""
        # Arrange
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.get_by_codigo.return_value = ProductoEntity(
            codigo="TEST001",
            descripcion="Test Product",
            marca="TestBrand",
            pvp=99.99,
            created_at=None,
            updated_at=None,
        )

        service = ProductoService(mock_repo)

        # Act
        result = service.obtener_producto("TEST001")

        # Assert
        assert result.codigo == "TEST001"
        assert result.descripcion == "Test Product"
        mock_repo.get_by_codigo.assert_called_once_with("TEST001")

    def test_obtener_producto_not_found(self):
        """Test getting non-existent product raises error."""
        # Arrange
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.get_by_codigo.side_effect = ProductoNotFoundException("TEST001")

        service = ProductoService(mock_repo)

        # Act & Assert
        with pytest.raises(ProductoNotFoundException):
            service.obtener_producto("TEST001")

    def test_eliminar_producto(self):
        """Test deleting product."""
        # Arrange
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.get_by_codigo.return_value = ProductoEntity(
            codigo="TEST001",
            descripcion="Test",
            marca="Test",
            pvp=99.99,
            created_at=None,
            updated_at=None,
        )
        mock_repo.delete.return_value = True

        service = ProductoService(mock_repo)

        # Act
        result = service.eliminar_producto("TEST001")

        # Assert
        assert result is True
        mock_repo.delete.assert_called_once_with("TEST001")

    def test_eliminar_producto_not_found(self):
        """Test deleting non-existent product returns False."""
        # Arrange
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.get_by_codigo.side_effect = ProductoNotFoundException("TEST001")

        service = ProductoService(mock_repo)

        # Act
        result = service.eliminar_producto("TEST001")

        # Assert
        assert result is False

    def test_get_all_productos(self):
        """Test getting all products with pagination."""
        # Arrange
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.get_all.return_value = [
            ProductoEntity(
                codigo="TEST001",
                descripcion="Product 1",
                marca="Test",
                familia=None,
                pvp=99.99,
                bc3_descripcion_corta=None,
                bc3_product_type=None,
                bc3_descripcion_completa=None,
                created_at=None,
                updated_at=None,
            ),
            ProductoEntity(
                codigo="TEST002",
                descripcion="Product 2",
                marca="Test",
                familia=None,
                pvp=199.99,
                bc3_descripcion_corta=None,
                bc3_product_type=None,
                bc3_descripcion_completa=None,
                created_at=None,
                updated_at=None,
            ),
        ]

        service = ProductoService(mock_repo)

        # Act
        result = service.get_all_productos(skip=0, limit=10)

        # Assert
        assert len(result) == 2
        mock_repo.get_all.assert_called_once_with(skip=0, limit=10)

    def test_count_productos(self):
        """Test getting total product count."""
        # Arrange
        mock_repo = Mock(spec=ProductoRepositoryInterface)
        mock_repo.count_total.return_value = 8288

        service = ProductoService(mock_repo)

        # Act
        result = service.count_productos()

        # Assert
        assert result == 8288
        mock_repo.count_total.assert_called_once()
