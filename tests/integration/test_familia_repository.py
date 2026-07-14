"""Integration tests for FamiliaRepository

Tests repository implementation with real database
."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.repositories.familia import SQLAlchemyFamiliaRepository
from app.domain.entities.familia import FamiliaEntity


class TestSQLAlchemyFamiliaRepositoryIntegration:
    """Tests for SQLAlchemyFamiliaRepository with real database."""

    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        engine = create_engine(
            "sqlite:///testing/testing.db",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()
        yield session
        session.close()

    def test_get_all_returns_familias_with_stats(self, db_session):
        """Test that get_all returns families with BC3 statistics."""
        repo = SQLAlchemyFamiliaRepository(db_session)
        familias = repo.get_all()

        # Should return some families
        assert isinstance(familias, list)
        assert len(familias) > 0

        # First family should have correct structure
        familia = familias[0]
        assert isinstance(familia, FamiliaEntity)
        assert familia.nombre
        assert familia.total_productos > 0
        assert familia.con_bc3 >= 0
        assert familia.con_imagen >= 0
        assert familia.descontinuados >= 0

    def test_get_by_nombre_returns_correct_familia(self, db_session):
        """Test that get_by_nombre returns correct family."""
        repo = SQLAlchemyFamiliaRepository(db_session)

        # Get all families first to find one
        familias = repo.get_all()
        if familias:
            test_nombre = familias[0].nombre
            familia = repo.get_by_nombre(test_nombre)

            assert familia.nombre == test_nombre
            assert isinstance(familia, FamiliaEntity)

    def test_get_by_nombre_raises_error_for_nonexistent(self, db_session):
        """Test that get_by_nombre raises error for non-existent family."""
        repo = SQLAlchemyFamiliaRepository(db_session)

        with pytest.raises(ValueError, match="no encontrada"):
            repo.get_by_nombre("XYZNonexistent")

    def test_get_statistics_returns_correct_stats(self, db_session):
        """Test that get_statistics returns aggregate statistics."""
        repo = SQLAlchemyFamiliaRepository(db_session)
        stats = repo.get_statistics()

        assert "total_familias" in stats
        assert "total_productos" in stats
        assert "bc3_coverage" in stats

        # Validate values
        assert stats["total_familias"] > 0
        assert stats["total_productos"] > 0
        assert 0 <= stats["bc3_coverage"] <= 100

    def test_statistics_data_consistency(self, db_session):
        """Test that statistics are consistent with individual families."""
        repo = SQLAlchemyFamiliaRepository(db_session)

        # Get individual families
        familias = repo.get_all()

        # Get aggregate statistics
        stats = repo.get_statistics()

        # Total families should match
        assert len(familias) == stats["total_familias"]

        # Total products should be sum of family totals
        calculated_total = sum(f.total_productos for f in familias)
        assert (
            calculated_total <= stats["total_productos"]
        )  # <= because some products may not have family
