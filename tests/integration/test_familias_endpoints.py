"""Integration tests for Familias endpoints

Tests HTTP interface with dependency injection using TDD approach
"""


class TestFamiliasEndpoints:
    """Tests for families HTTP endpoints"""

    def test_get_familias_success(self, client):
        """Test getting all families"""
        response = client.get("/api/familias/")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if data:
            familia = data[0]
            assert "nombre" in familia
            assert "total_productos" in familia
            assert "con_bc3" in familia

    def test_get_familias_with_limit(self, client):
        """Test getting families with limit parameter"""
        response = client.get("/api/familias/?limit=2")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 2

    def test_get_familias_invalid_limit(self, client):
        """Test validation of limit parameter"""
        response = client.get("/api/familias/?limit=0")  # Too low

        assert response.status_code == 422

    def test_get_familias_stats(self, client):
        """Test getting family statistics"""
        response = client.get("/api/familias/stats")

        assert response.status_code == 200
        stats = response.json()

        assert "total_familias" in stats
        assert "total_productos" in stats
        assert "bc3_coverage" in stats

        # Validate values
        assert stats["total_familias"] >= 0
        assert stats["total_productos"] >= 0
        assert 0 <= stats["bc3_coverage"] <= 100

    def test_get_familia_by_nombre_success(self, client):
        """Test getting family by name"""
        # First get all families to find a name
        all_response = client.get("/api/familias/")
        all_familias = all_response.json()

        if all_familias:
            test_nombre = all_familias[0]["nombre"]
            response = client.get(f"/api/familias/{test_nombre}")

            assert response.status_code == 200
            familia = response.json()
            assert familia["nombre"] == test_nombre

    def test_get_familia_by_nombre_not_found(self, client):
        """Test getting non-existent family returns 404"""
        response = client.get("/api/familias/XYZNonexistent")

        assert response.status_code == 404

    def test_get_top_bc3_coverage(self, client):
        """Test getting top BC3 coverage families"""
        response = client.get("/api/familias/top-bc3?limit=3")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 3

        if data:
            # Should have bc3_coverage_percentage field
            first = data[0]
            assert "bc3_coverage_percentage" in first
            assert 0 <= first["bc3_coverage_percentage"] <= 100

    def test_backward_compatibility_legacy_format(self, client):
        """Test that V1 format matches legacy router output"""
        response = client.get("/api/familias/")

        assert response.status_code == 200
        data = response.json()

        # V1 format expectations
        if data:
            familia = data[0]
            # These are the same fields as the legacy router
            assert "nombre" in familia
            assert "total_productos" in familia
