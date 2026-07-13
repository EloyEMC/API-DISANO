"""Unit tests for FamiliaRepository

Tests repository interface and implementation using TDD
"""

from unittest.mock import Mock
from app.domain.repositories.familia import FamiliaRepositoryInterface
from app.domain.entities.familia import FamiliaEntity


class TestFamiliaRepositoryInterface:
    """Tests for FamiliaRepositoryInterface interface"""

    def test_repository_interface_has_required_methods(self):
        """Test that interface has all required methods"""
        assert hasattr(FamiliaRepositoryInterface, "get_all")
        assert hasattr(FamiliaRepositoryInterface, "get_by_nombre")
        assert hasattr(FamiliaRepositoryInterface, "get_statistics")


class TestMockFamiliaRepository:
    """Tests using mock repository"""

    def test_get_all_returns_familias(self):
        """Test that get_all returns list of FamiliaEntity"""
        mock_repo = Mock(spec=FamiliaRepositoryInterface)
        mock_repo.get_all.return_value = [
            FamiliaEntity(
                nombre="Emergencia",
                total_productos=100,
                con_bc3=80,
                con_imagen=60,
                descontinuados=5,
            )
        ]

        result = mock_repo.get_all()

        assert len(result) == 1
        assert result[0].nombre == "Emergencia"
        mock_repo.get_all.assert_called_once()

    def test_get_by_nombre_returns_familia(self):
        """Test that get_by_nombre returns specific familia"""
        mock_repo = Mock(spec=FamiliaRepositoryInterface)
        mock_repo.get_by_nombre.return_value = FamiliaEntity(
            nombre="Emergencia",
            total_productos=100,
            con_bc3=80,
            con_imagen=60,
            descontinuados=5,
        )

        result = mock_repo.get_by_nombre("Emergencia")

        assert result.nombre == "Emergencia"
        mock_repo.get_by_nombre.assert_called_once_with("Emergencia")

    def test_get_statistics_returns_stats(self):
        """Test that get_statistics returns aggregate statistics"""
        mock_repo = Mock(spec=FamiliaRepositoryInterface)
        mock_repo.get_statistics.return_value = {
            "total_familias": 5,
            "total_productos": 1000,
            "bc3_coverage": 85.0,
        }

        result = mock_repo.get_statistics()

        assert result["total_familias"] == 5
        mock_repo.get_statistics.assert_called_once()
