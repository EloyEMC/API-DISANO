"""Integration tests for BC3 endpoints

Tests HTTP interface with dependency injection using TDD approach
"""


class TestBC3Endpoints:
    """Tests for BC3 HTTP endpoints"""

    def test_get_bc3_stats(self, client):
        """Test getting BC3 statistics"""
        response = client.get("/api/bc3/stats")

        assert response.status_code == 200
        stats = response.json()

        assert "total" in stats
        assert "con_descripcion_corta" in stats
        assert "con_descripcion_larga" in stats
        assert "con_tipo_producto" in stats

        # Validate values
        assert stats["total"] >= 0
        assert stats["con_descripcion_corta"] >= 0
        assert stats["con_descripcion_larga"] >= 0
        assert stats["con_tipo_producto"] >= 0

    def test_get_productos_por_tipo_bc3(self, client):
        """Test getting products by BC3 type"""
        response = client.get("/api/bc3/tipo/columna?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert "tipo" in data
        assert data["tipo"] == "columna"
        assert "total" in data
        assert "productos" in data
        assert isinstance(data["productos"], list)

    def test_get_columnas(self, client):
        """Test getting all columnas products"""
        response = client.get("/api/bc3/columnas?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "productos" in data
        assert isinstance(data["productos"], list)

    def test_get_articulaciones(self, client):
        """Test getting all articulaciones products"""
        response = client.get("/api/bc3/articulaciones?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "productos" in data
        assert isinstance(data["productos"], list)

    def test_get_bc3_descripcion_success(self, client):
        """Test getting BC3 description for existing product"""
        # First get a product to find one with BC3 data
        productos_response = client.get("/api/productos/v2/list?buscar=test&limit=10")
        if productos_response.status_code == 200:
            productos = productos_response.json()
            if productos and productos[0].get("bc3_descripcion_corta"):
                codigo = productos[0]["codigo"]
                response = client.get(f"/api/bc3/{codigo}")

                assert response.status_code == 200
                bc3_data = response.json()

                assert "codigo" in bc3_data
                assert "descripcion_corta" in bc3_data
                assert bc3_data["codigo"] == codigo

    def test_get_bc3_descripcion_not_found(self, client):
        """Test getting BC3 description for non-existent product"""
        response = client.get("/api/bc3/XYZNonexistent")

        assert response.status_code == 404

    def test_bc3_stats_data_consistency(self, client):
        """Test that BC3 statistics are consistent"""
        response = client.get("/api/bc3/stats")

        assert response.status_code == 200
        stats = response.json()

        # Total should be at least the sum of individual counts
        total = stats["total"]
        individual_sum = (
            stats["con_descripcion_corta"]
            + stats["con_descripcion_larga"]
            + stats["con_tipo_producto"]
        )

        # Individual counts can overlap, so sum can be > total
        assert individual_sum >= total or individual_sum == 0

    def test_backward_compatibility_legacy_format(self, client):
        """Test that V1 format matches legacy router output"""
        response = client.get("/api/bc3/stats")

        assert response.status_code == 200
        stats = response.json()

        # V1 format expectations - same keys as legacy
        expected_keys = [
            "total",
            "con_descripcion_corta",
            "con_descripcion_larga",
            "con_tipo_producto",
        ]
        for key in expected_keys:
            assert key in stats
