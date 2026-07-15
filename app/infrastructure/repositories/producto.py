from typing import List, Tuple

from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.domain.entities.producto import ProductoEntity
from app.domain.exceptions.not_found import ProductoNotFoundException
from app.domain.repositories.producto import ProductoRepositoryInterface
from app.infrastructure.models.producto_clean import ProductoModelClean as ProductoModel
from app.infrastructure.cache.pagination_cache import get_pagination_cache


class SQLAlchemyProductoRepository(ProductoRepositoryInterface):
    """
    SQLAlchemy implementation of Producto repository.

    This class implements the ProductoRepositoryInterface contract
    using SQLAlchemy ORM for database operations. It maps between
    domain entities (ProductoEntity) and database models (ProductoModel).
    """

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def get_by_codigo(self, codigo: str) -> ProductoEntity:
        """
        Get product by code.

        Args:
            codigo: Unique product identifier

        Returns:
            ProductoEntity: The found product

        Raises:
            ProductoNotFoundException: If product doesn't exist
        ."""
        model = (
            self.session.query(ProductoModel)
            .filter(ProductoModel.codigo == codigo)
            .first()
        )

        if not model:
            raise ProductoNotFoundException(codigo)

        return model.to_entity()

    def buscar_productos(
        self,
        termino: str = "",
        limit: int = 10,
        marca: str = "",
        familia: str = "",
    ) -> List[ProductoEntity]:
        """
        Search products with text search and filters.

        Args:
            termino: Search term (searches in description, code, BC3 fields)
            limit: Maximum number of results
            marca: Filter by brand
            familia: Filter by family

        Returns:
            List[ProductoEntity]: Matching products
        ."""
        query = self.session.query(ProductoModel)

        # Apply text search if term provided
        if termino:
            search_pattern = f"%{termino}%"
            query = query.filter(
                or_(
                    ProductoModel.descripcion.ilike(search_pattern),
                    ProductoModel.codigo.ilike(search_pattern),
                    ProductoModel.descripcion_corta.ilike(search_pattern),
                    ProductoModel.bc3_descripcion_corta.ilike(search_pattern),
                    ProductoModel.bc3_descripcion_completa.ilike(search_pattern),
                    ProductoModel.marca.ilike(search_pattern),
                    ProductoModel.familia.ilike(search_pattern),
                )
            )

        # Apply marca filter if provided
        if marca:
            query = query.filter(ProductoModel.marca == marca)

        # Apply familia filter if provided
        if familia:
            query = query.filter(ProductoModel.familia == familia)

        # Apply limit
        if limit > 0:
            query = query.limit(limit)

        # Convert models to entities
        return [model.to_entity() for model in query.all()]

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ProductoEntity]:
        """
        Get all products with pagination.

        Args:
            skip: Number of products to skip
            limit: Maximum number to return

        Returns:
            List[ProductoEntity]: Products in specified range
        """
        query = self.session.query(ProductoModel).offset(skip).limit(limit)
        return [model.to_entity() for model in query.all()]

    def save(self, producto: ProductoEntity) -> ProductoEntity:
        """
        Save product (create or update).

        Args:
            producto: Product entity to save

        Returns:
            ProductoEntity: Saved product with any DB-generated fields
        """
        # Create model from entity
        model = ProductoModel.from_entity(producto)

        # Use merge to handle both create and update
        self.session.merge(model)
        self.session.flush()  # Flush without commit

        return model.to_entity()

    def delete(self, codigo: str) -> bool:
        """
        Delete product by code.

        Args:
            codigo: Product identifier to delete

        Returns:
            bool: True if deleted, False if not found
        """
        model = (
            self.session.query(ProductoModel)
            .filter(ProductoModel.codigo == codigo)
            .first()
        )

        if not model:
            return False

        self.session.delete(model)
        self.session.flush()

        return True

    def count_total(self) -> int:
        """
        Get total count of products.

        Returns:
            int: Total number of products in database
        """
        return self.session.query(ProductoModel).count()

    def buscar_productos_paginado(self, dto: dict) -> Tuple[List[ProductoEntity], int]:
        """Execute paginated query with sorting and filtering.

        This method wraps the actual query with caching logic to improve
        performance for frequently accessed pagination queries.

        Args:
            dto: Complete pagination request DTO with filters and sorting

        Returns:
            Tuple[list[ProductoEntity], int]:
                - List of entities for current page
                - Total count of matching items
        ."""
        # Get pagination cache wrapper
        cache = get_pagination_cache()

        # Extract parameters for cache key
        page = dto.get("page", 1)
        per_page = dto.get("per_page", 10)
        sort = dto.get("sort")
        filters = dto.get("filters", {})

        # Try to get from cache first
        cached_result = cache.get("productos", page, per_page, sort, filters)
        if cached_result is not None:
            # Convert cached data back to entities
            entities_data = cached_result.get("entities", [])
            total_count = cached_result.get("total", 0)
            entities = [ProductoEntity(**data) for data in entities_data]
            return entities, total_count

        # Cache miss - execute actual query
        entities, total_count = self._execute_pagination_query(dto)

        # Cache the result
        cache_data = {
            "entities": [entity.model_dump() for entity in entities],
            "total": total_count,
        }
        cache.set("productos", page, per_page, sort, filters, cache_data)

        return entities, total_count

    def _execute_pagination_query(self, dto: dict) -> Tuple[List[ProductoEntity], int]:
        """Execute the actual pagination query (without caching).

        This is the internal query execution method that can be reused
        by the cached wrapper method.

        Args:
            dto: Complete pagination request DTO with filters and sorting

        Returns:
            Tuple[list[ProductoEntity], int]:
                - List of entities for current page
                - Total count of matching items
        ."""
        # Base query
        query = self.session.query(ProductoModel)

        # Apply filters
        filters = dto.get("filters", {})
        if filters.get("marca"):
            query = query.filter(ProductoModel.marca == filters["marca"])

        if filters.get("familia"):
            query = query.filter(ProductoModel.familia == filters["familia"])

        if filters.get("pvp_min") is not None:
            query = query.filter(ProductoModel.pvp >= filters["pvp_min"])

        if filters.get("pvp_max") is not None:
            query = query.filter(ProductoModel.pvp <= filters["pvp_max"])

        if filters.get("bc3_product_type"):
            query = query.filter(
                ProductoModel.bc3_product_type == filters["bc3_product_type"]
            )

        if filters.get("bc3_has_descripcion_corta") is not None:
            if filters["bc3_has_descripcion_corta"]:
                query = query.filter(ProductoModel.bc3_descripcion_corta.isnot(None))
            else:
                query = query.filter(ProductoModel.bc3_descripcion_corta.is_(None))

        if filters.get("buscar"):
            query = self._apply_text_search(query, filters["buscar"])

        # Get total count BEFORE pagination
        total_count = query.count()

        # Apply sorting
        sort_string = dto.get("sort")
        if sort_string:
            query = self._apply_sorting(query, sort_string)

        # Apply pagination
        query = query.offset(dto["offset"]).limit(dto["per_page"])

        # Execute query
        models = query.all()

        # Convert to entities
        entities = [model.to_entity() for model in models]

        return entities, total_count

    def _apply_sorting(self, query, sort_string: str):
        """Apply sorting to query."""
        parts = sort_string.split(":")
        field = parts[0]
        order = parts[1].lower() if len(parts) > 1 else "asc"

        field_mapping = {
            "codigo": ProductoModel.codigo,
            "descripcion": ProductoModel.descripcion,
            "marca": ProductoModel.marca,
            "familia": ProductoModel.familia,
            "pvp": ProductoModel.pvp,
            "bc3_descripcion_corta": ProductoModel.bc3_descripcion_corta,
            "bc3_product_type": ProductoModel.bc3_product_type,
        }

        if field in field_mapping:
            order_func = desc if order == "desc" else asc
            return query.order_by(order_func(field_mapping[field]))

        return query

    def _apply_text_search(self, query, search_pattern: str):
        """Apply text search to query."""
        pattern = f"%{search_pattern}%"
        return query.filter(
            or_(
                ProductoModel.codigo.ilike(pattern),
                ProductoModel.descripcion.ilike(pattern),
                ProductoModel.descripcion_corta.ilike(pattern),
                ProductoModel.bc3_descripcion_corta.ilike(pattern),
                ProductoModel.bc3_descripcion_completa.ilike(pattern),
            )
        )
