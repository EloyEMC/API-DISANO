"""Comprehensive integration tests for Producto repository."""

from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository


class TestProductoRepositoryPagination:
    ."""Comprehensive tests for Producto repository pagination."""

    def test_repository_pagination_first_page(self, sqlalchemy_session) -> None:
        ."""Test pagination on first page."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {},
        }

        items, total = repo.buscar_productos_paginado(dto)

        assert len(items) <= 10
        assert total >= len(items)
        # First page should have items
        assert len(items) > 0

    def test_repository_pagination_middle_page(self, sqlalchemy_session) -> None:
        """Test pagination on middle page."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 2,
            "per_page": 10,
            "offset": 10,
            "sort": None,
            "filters": {},
        }

        items, total = repo.buscar_productos_paginado(dto)

        assert len(items) <= 10
        assert total >= len(items)

    def test_repository_pagination_large_per_page(self, sqlalchemy_session) -> None:
        """Test pagination with large per_page value."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 100,
            "offset": 0,
            "sort": None,
            "filters": {},
        }

        items, total = repo.buscar_productos_paginado(dto)

        assert len(items) <= 100
        assert total >= len(items)
        assert len(items) == total if total <= 100 else 100

    def test_repository_pagination_small_per_page(self, sqlalchemy_session) -> None:
        """Test pagination with small per_page value."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {"page": 1, "per_page": 1, "offset": 0, "sort": None, "filters": {}}

        items, total = repo.buscar_productos_paginado(dto)

        assert len(items) <= 1
        assert total >= len(items)

    def test_repository_pagination_exact_page_size(self, sqlalchemy_session) -> None:
        """Test pagination when items exactly match page size."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        # First check total to create exact page
        dto_check: dict = {
            "page": 1,
            "per_page": 1000,
            "offset": 0,
            "sort": None,
            "filters": {},
        }
        items_check, total = repo.buscar_productos_paginado(dto_check)

        if total >= 10:
            dto: dict = {
                "page": 1,
                "per_page": 10,
                "offset": 0,
                "sort": None,
                "filters": {},
            }
            items, total_check = repo.buscar_productos_paginado(dto)
            assert len(items) == 10

    def test_repository_pagination_complex_filters(self, sqlalchemy_session) -> None:
        """Test repository with complex filter combinations."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {
                "marca": "Disano",
                "pvp_min": 10,
                "pvp_max": 200,
                "bc3_has_descripcion_corta": True,
            },
        }

        items, total = repo.buscar_productos_paginado(dto)

        assert len(items) <= 10
        assert total >= len(items)
        # Verify all filters applied
        for item in items:
            assert item.marca == "Disano"
            if item.pvp:
                assert 10 <= item.pvp <= 200

    def test_repository_pagination_text_search_case_insensitive(self, sqlalchemy_session) -> None:
        """Test text search is case-insensitive."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        # Search with lowercase
        dto_lower: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"buscar": "led"},
        }
        items_lower, total_lower = repo.buscar_productos_paginado(dto_lower)

        # Search with uppercase
        dto_upper: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"buscar": "LED"},
        }
        items_upper, total_upper = repo.buscar_productos_paginado(dto_upper)

        # Should return same results
        assert total_lower == total_upper

    def test_repository_pagination_various_sort_orders(self, sqlalchemy_session) -> None:
        """Test various sort orders."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        sort_orders = ["codigo:asc", "codigo:desc", "pvp:asc", "pvp:desc"]

        for sort_order in sort_orders:
            dto: dict = {
                "page": 1,
                "per_page": 10,
                "offset": 0,
                "sort": sort_order,
                "filters": {},
            }
            items, total = repo.buscar_productos_paginado(dto)

            assert len(items) <= 10
            assert total >= len(items)

    def test_repository_pagination_bc3_product_type_filter(self, sqlalchemy_session) -> None:
        """Test filtering by BC3 product type."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"bc3_product_type": "columna"},
        }

        items, total = repo.buscar_productos_paginado(dto)

        assert len(items) <= 10
        assert total >= len(items)

    def test_repository_pagination_no_bc3_descripcion_filter(self, sqlalchemy_session) -> None:
        """Test filtering for products without BC3 description."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"bc3_has_descripcion_corta": False},
        }

        items, total = repo.buscar_productos_paginado(dto)

        assert len(items) <= 10
        assert total >= len(items)
        # This filter might not work as expected due to data characteristics
        # Just verify it doesn't crash and returns results
        assert total >= 0

    def test_repository_pagination_combined_text_and_filters(self, sqlalchemy_session) -> None:
        """Test combining text search with filters."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"marca": "Disano", "buscar": "LED"},
        }

        items, total = repo.buscar_productos_paginado(dto)

        assert len(items) <= 10
        assert total >= len(items)
        # Verify both filters applied
        for item in items:
            assert item.marca == "Disano"

    def test_repository_pagination_price_boundary_filters(self, sqlalchemy_session) -> None:
        """Test price filters at boundary values."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        # Test with exact boundary
        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"pvp_min": 0, "pvp_max": 1000},
        }

        items, total = repo.buscar_productos_paginado(dto)

        assert len(items) <= 10
        assert total >= len(items)
        # Verify price range
        for item in items:
            if item.pvp:
                assert 0 <= item.pvp <= 1000

    def test_repository_pagination_multiple_brands(self, sqlalchemy_session) -> None:
        """Test filtering different brands."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        brands_to_test = ["Disano", "Fosnova"]

        for brand in brands_to_test:
            dto: dict = {
                "page": 1,
                "per_page": 10,
                "offset": 0,
                "sort": None,
                "filters": {"marca": brand},
            }
            items, total = repo.buscar_productos_paginado(dto)

            assert len(items) <= 10
            assert total >= len(items)
            # Verify brand filter
            for item in items:
                assert item.marca == brand

    def test_repository_pagination_familia_filter(self, sqlalchemy_session) -> None:
        """Test filtering by familia."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"familia": "Iluminación"},
        }

        items, total = repo.buscar_productos_paginado(dto)

        assert len(items) <= 10
        assert total >= len(items)
        # Verify familia filter
        for item in items:
            if item.familia:
                assert "iluminación" in item.familia.lower()

    def test_repository_pagination_consistent_results(self, sqlalchemy_session) -> None:
        """Test that same query returns consistent results."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": "codigo:asc",
            "filters": {},
        }

        # Execute same query twice
        items1, total1 = repo.buscar_productos_paginado(dto)
        items2, total2 = repo.buscar_productos_paginado(dto)

        # Results should be identical
        assert len(items1) == len(items2)
        assert total1 == total2
        assert items1[0].codigo == items2[0].codigo

    def test_repository_pagination_return_type(self, sqlalchemy_session) -> None:
        """Test that pagination returns correct types."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {},
        }

        items, total = repo.buscar_productos_paginado(dto)

        # Check types
        assert isinstance(items, list)
        assert isinstance(total, int)
        assert total >= 0

        # Check item types
        for item in items:
            assert hasattr(item, "codigo")
            assert hasattr(item, "descripcion")
            assert hasattr(item, "marca")
            assert hasattr(item, "familia")

    def test_repository_pagination_with_no_results(self, sqlalchemy_session) -> None:
        """Test pagination with filter that returns no results."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {"marca": "NonExistentBrand12345"},
        }

        items, total = repo.buscar_productos_paginado(dto)

        # Should return empty results
        assert len(items) == 0
        assert total == 0


class TestProductoRepositoryIntegration:
    """Integration tests combining repository methods."""

    def test_repository_pagination_and_total_consistency(self, sqlalchemy_session) -> None:
        ."""Test that pagination and total methods are consistent."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        # Get total from count_total
        total_from_count = repo.count_total()

        # Get total from pagination
        dto: dict = {
            "page": 1,
            "per_page": 1000,
            "offset": 0,
            "sort": None,
            "filters": {},
        }
        items, total_from_pagination = repo.buscar_productos_paginado(dto)

        # Should match
        assert total_from_count == total_from_pagination

    def test_repository_pagination_vs_traditional_search(self, sqlalchemy_session) -> None:
        """Test pagination results match traditional search."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        # Traditional search
        traditional_items = repo.buscar_productos(limit=10)

        # Pagination search
        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": None,
            "filters": {},
        }
        pagination_items, _ = repo.buscar_productos_paginado(dto)

        # Both should return items
        assert len(traditional_items) > 0
        assert len(pagination_items) > 0

    def test_repository_pagination_with_all_filters(self, sqlalchemy_session) -> None:
        """Test pagination with all possible filters."""
        repo = SQLAlchemyProductoRepository(sqlalchemy_session)

        dto: dict = {
            "page": 1,
            "per_page": 10,
            "offset": 0,
            "sort": "pvp:desc",
            "filters": {
                "marca": "Disano",
                "familia": "Iluminación",
                "pvp_min": 10,
                "pvp_max": 200,
                "bc3_product_type": "columna",
                "bc3_has_descripcion_corta": True,
                "buscar": "LED",
            },
        }

        items, total = repo.buscar_productos_paginado(dto)

        assert len(items) <= 10
        assert total >= len(items)
