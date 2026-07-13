"""SQLAlchemy implementation of FamiliaRepository

Repository implementation using SQLAlchemy ORM for data access.
"""

from typing import List, Dict, Any, Tuple
from sqlalchemy import func, case, asc, desc, or_
from sqlalchemy.orm import Session

from app.domain.repositories.familia import FamiliaRepositoryInterface
from app.domain.entities.familia import FamiliaEntity
from app.infrastructure.models.producto_clean import ProductoModelClean as ProductoModel
from app.infrastructure.cache.pagination_cache import get_pagination_cache


class SQLAlchemyFamiliaRepository(FamiliaRepositoryInterface):
    """SQLAlchemy implementation for FamiliaRepository"""

    def __init__(self, session: Session):
        """
        Initialize repository with database session

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def get_all(self) -> List[FamiliaEntity]:
        """
        Get all families with BC3 statistics from productos_clean view

        Returns:
            List[FamiliaEntity]: All families with BC3 statistics
        """
        # Group by familia and calculate statistics
        query = (
            self.session.query(
                ProductoModel.familia,
                func.count(ProductoModel.codigo).label("total_productos"),
                func.sum(
                    case((ProductoModel.bc3_descripcion_corta.isnot(None), 1), else_=0)
                ).label("con_bc3"),
                func.sum(
                    case((ProductoModel.descripcion_corta.isnot(None), 1), else_=0)
                ).label("con_imagen"),
            )
            .filter(ProductoModel.familia.isnot(None))
            .group_by(ProductoModel.familia)
            .order_by(ProductoModel.familia)
        )

        results = query.all()

        # Convert to domain entities
        return [
            FamiliaEntity(
                nombre=row.familia,
                total_productos=row.total_productos,
                con_bc3=int(row.con_bc3 or 0),
                con_imagen=int(row.con_imagen or 0),
                descontinuados=0,  # Not in clean view
            )
            for row in results
        ]

    def get_by_nombre(self, nombre: str) -> FamiliaEntity:
        """
        Get family by name with statistics

        Args:
            nombre: Family name

        Returns:
            FamiliaEntity: Family with statistics

        Raises:
            ValueError: If family not found
        """
        query = (
            self.session.query(
                ProductoModel.familia,
                func.count(ProductoModel.codigo).label("total_productos"),
                func.sum(
                    case((ProductoModel.bc3_descripcion_corta.isnot(None), 1), else_=0)
                ).label("con_bc3"),
                func.sum(
                    case((ProductoModel.descripcion_corta.isnot(None), 1), else_=0)
                ).label("con_imagen"),
            )
            .filter(ProductoModel.familia == nombre)
            .group_by(ProductoModel.familia)
        )

        row = query.first()

        if not row:
            raise ValueError(f"Familia '{nombre}' no encontrada")

        return FamiliaEntity(
            nombre=row.familia,
            total_productos=row.total_productos,
            con_bc3=int(row.con_bc3 or 0),
            con_imagen=int(row.con_imagen or 0),
            descontinuados=0,  # Not in clean view
        )

    def get_statistics(self) -> Dict:
        """
        Get aggregate statistics across all families

        Returns:
            Dict: Aggregate statistics including total families, products, BC3 coverage
        """
        # Total families
        total_familias_query = self.session.query(
            func.count(func.distinct(ProductoModel.familia))
        ).filter(ProductoModel.familia.isnot(None))
        total_familias = total_familias_query.scalar() or 0

        # Total products
        total_productos = (
            self.session.query(func.count(ProductoModel.codigo)).scalar() or 0
        )

        # BC3 coverage
        bc3_coverage_query = self.session.query(
            func.count(ProductoModel.codigo).label("total"),
            func.sum(
                case((ProductoModel.bc3_descripcion_corta.isnot(None), 1), else_=0)
            ).label("con_bc3"),
        )
        result = bc3_coverage_query.first()

        bc3_coverage = 0.0
        if result and result.total > 0:
            bc3_coverage = (result.con_bc3 / result.total) * 100

            return {
                "total_familias": total_familias,
                "total_productos": total_productos,
                "bc3_coverage": round(bc3_coverage, 2),
            }

    def buscar_familias_paginado(self, dto: dict) -> Tuple[List[FamiliaEntity], int]:
        """Search families with pagination, sorting, and filtering.

        This method wraps the actual query with caching logic to improve
        performance for frequently accessed pagination queries.

        Args:
            dto: Complete pagination request DTO with filters and sorting

        Returns:
            tuple[list[FamiliaEntity], int]:
                - List of entities for current page
                - Total count of matching items
        """
        # Get pagination cache wrapper
        cache = get_pagination_cache()

        # Extract parameters for cache key
        page = dto.get("page", 1)
        per_page = dto.get("per_page", 10)
        sort = dto.get("sort")
        filters = dto.get("filters", {})

        # Try to get from cache first
        cached_result = cache.get("familias", page, per_page, sort, filters)
        if cached_result is not None:
            # Convert cached data back to entities
            entities_data = cached_result.get("entities", [])
            total_count = cached_result.get("total", 0)
            entities = [FamiliaEntity(**data) for data in entities_data]
            return entities, total_count

        # Cache miss - execute actual query
        entities, total_count = self._execute_pagination_query(dto)

        # Cache the result
        cache_data = {
            "entities": [entity.model_dump() for entity in entities],
            "total": total_count,
        }
        cache.set("familias", page, per_page, sort, filters, cache_data)

        return entities, total_count

    def _execute_pagination_query(self, dto: dict) -> Tuple[List[FamiliaEntity], int]:
        """Execute the actual pagination query (without caching).

        This is the internal query execution method that can be reused
        by the cached wrapper method.

        Args:
            dto: Complete pagination request DTO with filters and sorting

        Returns:
            tuple[list[FamiliaEntity], int]:
                - List of entities for current page
                - Total count of matching items
        """
        # Build base query with grouping
        base_query = (
            self.session.query(
                ProductoModel.familia,
                func.count(ProductoModel.codigo).label("total_productos"),
                func.sum(
                    case((ProductoModel.bc3_descripcion_corta.isnot(None), 1), else_=0)
                ).label("con_bc3"),
                func.sum(
                    case((ProductoModel.descripcion_corta.isnot(None), 1), else_=0)
                ).label("con_imagen"),
            )
            .filter(ProductoModel.familia.isnot(None))
            .group_by(ProductoModel.familia)
        )

        # Apply filters
        filters = dto.get("filters", {})
        if filters.get("buscar"):
            search_pattern = f"%{filters['buscar']}%"
            base_query = base_query.filter(
                or_(ProductoModel.familia.ilike(search_pattern))
            )

        # Get total count BEFORE pagination
        total_count = base_query.count()

        # Apply sorting
        sort_string = dto.get("sort")
        if sort_string:
            base_query = self._apply_sorting(base_query, sort_string)
        else:
            base_query = base_query.order_by(asc(ProductoModel.familia))

        # Apply pagination
        base_query = base_query.offset(dto["offset"]).limit(dto["per_page"])

        # Execute query
        results = base_query.all()

        # Convert to domain entities
        entities = [
            FamiliaEntity(
                nombre=row.familia,
                total_productos=row.total_productos,
                con_bc3=int(row.con_bc3 or 0),
                con_imagen=int(row.con_imagen or 0),
                descontinuados=0,  # Not in clean view
            )
            for row in results
        ]

        return entities, total_count

    def _apply_sorting(self, query, sort_string: str) -> Any:
        """Apply sorting to query."""
        parts = sort_string.split(":")
        field = parts[0]
        order = parts[1].lower() if len(parts) > 1 else "asc"

        field_mapping = {
            "nombre": ProductoModel.familia,
            "familia": ProductoModel.familia,
            "total_productos": "total_productos",
            "con_bc3": "con_bc3",
            "con_imagen": "con_imagen",
        }

        if field in field_mapping:
            order_func = desc if order == "desc" else asc
            mapped_field = field_mapping[field]

            if isinstance(mapped_field, str):
                # Aggregated fields need different handling
                return query.order_by(order_func(mapped_field))
            else:
                return query.order_by(order_func(mapped_field))

        return query
