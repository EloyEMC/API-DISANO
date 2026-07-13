"""Test ProductoRepositoryInterface has pagination method."""


def test_producto_repository_interface_pagination_method() -> None:
    """Test that ProductoRepositoryInterface has pagination method."""
    from app.domain.repositories.producto import ProductoRepositoryInterface

    # Check that the interface has the pagination method
    assert hasattr(ProductoRepositoryInterface, "buscar_productos_paginado")
    method = getattr(ProductoRepositoryInterface, "buscar_productos_paginado")

    # Check that it's abstract
    assert hasattr(method, "__isabstractmethod__")
