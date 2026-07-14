"""Repository interface for Producto

Defines the contract for Producto data access.
Following Dependency Inversion Principle: infrastructure depends on this interface.
."""

from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.producto import ProductoEntity


class ProductoRepositoryInterface(ABC):
    """Interface for Producto repository

    This interface defines the contract for data access operations
    on Product entities. Implementations (e.g., SQLAlchemy) depend
    on this interface, not vice versa.

    Methods:
        get_by_codigo: Retrieve product by unique code
        buscar_productos: Search products with filters
        get_all: Retrieve all products with pagination
        save: Create or update product
        delete: Remove product
    """

    @abstractmethod
    def get_by_codigo(self, codigo: str) -> ProductoEntity:
        """Get product by code

        Args:
            codigo: Unique product identifier

        Returns:
            ProductoEntity: The found product

        Raises:
            ProductoNotFoundException: If product doesn't exist
        ."""
        pass

    @abstractmethod
    def buscar_productos(
        self,
        termino: str = "",
        limit: int = 10,
        marca: str = "",
        familia: str = "",
    ) -> List[ProductoEntity]:
        """Search products with text search and filters

        Args:
            termino: Search term (searches in description, code, BC3 fields)
            limit: Maximum number of results
            marca: Filter by brand
            familia: Filter by family

        Returns:
            List[ProductoEntity]: Matching products
        """
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ProductoEntity]:
        """Get all products with pagination

        Args:
            skip: Number of products to skip
            limit: Maximum number to return

        Returns:
            List[ProductoEntity]: Products in specified range
        """
        pass

    @abstractmethod
    def save(self, producto: ProductoEntity) -> ProductoEntity:
        """Save product (create or update)

        Args:
            producto: Product entity to save

        Returns:
            ProductoEntity: Saved product with any DB-generated fields
        """
        pass

    @abstractmethod
    def delete(self, codigo: str) -> bool:
        """Delete product by code

        Args:
            codigo: Product identifier to delete

        Returns:
            bool: True if deleted, False if not found
        """
        pass

    @abstractmethod
    def count_total(self) -> int:
        """Get total count of products

        Returns:
            int: Total number of products in database
        """
        pass

    @abstractmethod
    def buscar_productos_paginado(self, dto: dict) -> tuple[list[ProductoEntity], int]:
        """Search products with pagination, sorting, and filtering

        Args:
            dto: Complete pagination request DTO with filters and sorting

        Returns:
            tuple[list[ProductoEntity], int]:
                - List of entities for current page
                - Total count of matching items
        ."""
        pass
