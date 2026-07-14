"""Unit tests for FamiliaEntity

Domain entity for Familia - using TDD approach
."""

import pytest
from app.domain.entities.familia import FamiliaEntity


class TestFamiliaEntity:
    """Tests for FamiliaEntity domain entity."""

    def test_familia_entity_creation_success(self):
        """Test creating a familia entity with valid data."""
        entity = FamiliaEntity(
            nombre="Emergencia",
            total_productos=100,
            con_bc3=80,
            con_imagen=60,
            descontinuados=5,
        )

        assert entity.nombre == "Emergencia"
        assert entity.total_productos == 100
        assert entity.con_bc3 == 80
        assert entity.con_imagen == 60
        assert entity.descontinuados == 5

    def test_familia_entity_minimal(self):
        """Test creating familia with minimal fields."""
        entity = FamiliaEntity(
            nombre="Test", total_productos=1, con_bc3=0, con_imagen=0, descontinuados=0
        )

        assert entity.nombre == "Test"
        assert entity.total_productos == 1

    def test_familia_entity_validation_nombre_required(self):
        """Test that nombre is required."""
        with pytest.raises(Exception):
            FamiliaEntity(
                nombre="",  # Empty string
                total_productos=10,
                con_bc3=5,
                con_imagen=5,
                descontinuados=0,
            )

    def test_familia_entity_validation_negative_counts(self):
        """Test that counts cannot be negative."""
        with pytest.raises(Exception):
            FamiliaEntity(
                nombre="Test",
                total_productos=-1,  # Negative
                con_bc3=0,
                con_imagen=0,
                descontinuados=0,
            )

    def test_familia_entity_calculated_fields(self):
        """Test that we can calculate derived statistics."""
        entity = FamiliaEntity(
            nombre="Test",
            total_productos=100,
            con_bc3=80,
            con_imagen=60,
            descontinuados=5,
        )

        # Calculated fields
        bc3_coverage = (entity.con_bc3 / entity.total_productos) * 100
        assert bc3_coverage == 80.0

    def test_familia_entity_immutable(self):
        """Test that FamiliaEntity is immutable."""
        entity = FamiliaEntity(
            nombre="Test", total_productos=10, con_bc3=5, con_imagen=5, descontinuados=0
        )

        with pytest.raises(Exception):
            entity.nombre = "Modified"  # Should fail (immutable)
