"""Unit tests for FamiliaService

Tests business logic and aggregation rules using TDD approach
"""

from unittest.mock import Mock

from app.domain.services.familia import FamiliaService
from app.domain.repositories.familia import FamiliaRepositoryInterface
from app.domain.entities.familia import FamiliaEntity


class TestFamiliaService:
    """Tests for FamiliaService business logic"""

    def test_get_all_familias(self):
        """Test getting all families"""
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

        service = FamiliaService(mock_repo)
        result = service.get_all_familias()

        assert len(result) == 1
        assert result[0].nombre == "Emergencia"
        mock_repo.get_all.assert_called_once()

    def test_get_familia_by_nombre(self):
        """Test getting family by name"""
        mock_repo = Mock(spec=FamiliaRepositoryInterface)
        mock_repo.get_by_nombre.return_value = FamiliaEntity(
            nombre="Emergencia",
            total_productos=100,
            con_bc3=80,
            con_imagen=60,
            descontinuados=5,
        )

        service = FamiliaService(mock_repo)
        result = service.get_familia_by_nombre("Emergencia")

        assert result.nombre == "Emergencia"
        mock_repo.get_by_nombre.assert_called_once_with("Emergencia")

    def test_get_statistics(self):
        """Test getting aggregate statistics"""
        mock_repo = Mock(spec=FamiliaRepositoryInterface)
        mock_repo.get_statistics.return_value = {
            "total_familias": 5,
            "total_productos": 1000,
            "bc3_coverage": 85.0,
        }

        service = FamiliaService(mock_repo)
        result = service.get_statistics()

        assert result["total_familias"] == 5
        mock_repo.get_statistics.assert_called_once()

    def test_get_bc3_coverage_leaderboard(self):
        """Test getting BC3 coverage leaderboard"""
        mock_repo = Mock(spec=FamiliaRepositoryInterface)
        mock_repo.get_all.return_value = [
            FamiliaEntity(
                nombre="Emergencia",
                total_productos=100,
                con_bc3=90,  # 90%
                con_imagen=80,
                descontinuados=2,
            ),
            FamiliaEntity(
                nombre="Interiores",
                total_productos=200,
                con_bc3=160,  # 80%
                con_imagen=150,
                descontinuados=10,
            ),
            FamiliaEntity(
                nombre="Exteriores",
                total_productos=50,
                con_bc3=25,  # 50%
                con_imagen=30,
                descontinuados=5,
            ),
        ]

        service = FamiliaService(mock_repo)
        leaderboard = service.get_bc3_coverage_leaderboard(limit=2)

        assert len(leaderboard) == 2
        assert leaderboard[0].nombre == "Emergencia"  # Highest BC3 coverage
        assert leaderboard[1].nombre == "Interiores"
        mock_repo.get_all.assert_called_once()

    def test_bc3_coverage_calculation(self):
        """Test that BC3 coverage is calculated correctly"""
        familia = FamiliaEntity(
            nombre="Test",
            total_productos=100,
            con_bc3=75,
            con_imagen=60,
            descontinuados=5,
        )

        coverage = familia.get_bc3_coverage_percentage()
        assert coverage == 75.0
