"""Domain service for Producto

Business logic layer that coordinates repositories and applies domain rules.
."""

from app.domain.entities.producto import ProductoEntity
from app.domain.exceptions.not_found import (
    ProductoNotFoundException,
    ProductoYaExisteException,
    ValidationException,
)
from app.domain.repositories.producto import ProductoRepositoryInterface
from app.application.dto.producto import (
    ProductoCreateDTO,
    ProductoSearchDTO,
    ProductoUpdateDTO,
)
from app.application.dto.pagination import (
    PaginationRequestDTO,
    PaginatedResponseDTO,
    PaginationMetadata,
)


class ProductoService:
    """
    Business logic service for Producto.

    This service contains business rules and validation logic.
    It uses the repository interface for data access, maintaining
    dependency inversion and testability.
    """

    def __init__(self, repository: ProductoRepositoryInterface):
        """
        Initialize service with repository.

        Args:
            repository: Producto repository implementation
        """
        self.repository = repository

    def crear_producto(self, dto: ProductoCreateDTO) -> ProductoEntity:
        """
        Create new product with business rules.

        Business rules:
        1. Validate input fields (DTO validation + business rules)
        2. Check for duplicate code
        3. Create and persist entity

        Args:
            dto: Product creation data

        Returns:
            ProductoEntity: Created product

        Raises:
            ValidationException: If validation fails
            ProductoYaExisteException: If code already exists
        ."""
        # 1. Validations
        if len(dto.descripcion) < 2:
            raise ValidationException("descripcion", "Mínimo 2 caracteres")

        if dto.pvp and dto.pvp < 0:
            raise ValidationException("pvp", "No puede ser negativo")

        if len(dto.marca) < 1:
            raise ValidationException("marca", "Mínimo 1 caracter")

        # 2. Check uniqueness
        try:
            self.repository.get_by_codigo(dto.codigo)
            raise ProductoYaExisteException(dto.codigo)
        except ProductoNotFoundException:
            pass  # OK, product doesn't exist

        # 3. Create entity from DTO
        producto = dto.to_entity()

        # 4. Persist through repository
        return self.repository.save(producto)

    def actualizar_producto(
        self, codigo: str, dto: ProductoUpdateDTO
    ) -> ProductoEntity:
        """
        Update existing product.

        Args:
            codigo: Product identifier
            dto: Product update data (partial)

        Returns:
            ProductoEntity: Updated product

        Raises:
            ProductoNotFoundException: If product doesn't exist
            ValidationException: If validation fails
        ."""
        # 1. Get existing
        existing = self.repository.get_by_codigo(codigo)

        # 2. Apply updates (only fields provided)
        update_data = dto.model_dump(exclude_unset=True)

        # Validate updated fields
        if "pvp" in update_data and update_data["pvp"] < 0:
            raise ValidationException("pvp", "No puede ser negativo")

        # 3. Create updated entity (inmutable, so create new instance)
        updated_dict = existing.model_dump()
        updated_dict.update(update_data)
        updated_producto = ProductoEntity(**updated_dict)

        # 4. Persist
        return self.repository.save(updated_producto)

    def buscar_productos(self, dto: ProductoSearchDTO) -> list[ProductoEntity]:
        """
        Search products with filters.

        Args:
            dto: Search parameters with filters

        Returns:
            list[ProductoEntity]: Matching products
        ."""
        return self.repository.buscar_productos(
            termino=dto.buscar or "",
            limit=dto.limit,
            marca=dto.marca or "",
            familia=dto.familia or "",
        )

    def obtener_producto(self, codigo: str) -> ProductoEntity:
        """
        Get product by code.

        Args:
            codigo: Product identifier

        Returns:
            ProductoEntity: Found product

        Raises:
            ProductoNotFoundException: If not found
        """
        return self.repository.get_by_codigo(codigo)

    def eliminar_producto(self, codigo: str) -> bool:
        """
        Delete product by code.

        Args:
            codigo: Product identifier

        Returns:
            bool: True if deleted, False if not found
        """
        # 1. Verify exists
        try:
            self.repository.get_by_codigo(codigo)
        except ProductoNotFoundException:
            return False

        # 2. Delete
        return self.repository.delete(codigo)

    def get_all_productos(
        self, skip: int = 0, limit: int = 100
    ) -> list[ProductoEntity]:
        """
        Get all products with pagination.

        Args:
            skip: Number to skip
            limit: Maximum to return

        Returns:
            list[ProductoEntity]: Products in range
        """
        return self.repository.get_all(skip=skip, limit=limit)

    def count_productos(self) -> int:
        """
        Get total product count.

        Returns:
            int: Total number of products
        """
        return self.repository.count_total()

    def buscar_productos_paginado(
        self, request_dto: PaginationRequestDTO
    ) -> PaginatedResponseDTO:
        """Search products with pagination, sorting, and filtering.

        Args:
            request_dto: Pagination request with filters and sorting

        Returns:
            PaginatedResponseDTO: Products with pagination metadata
        ."""
        # Convert DTO to dict format for repository
        dto_dict: dict = {
            "page": request_dto.page,
            "per_page": request_dto.per_page,
            "offset": request_dto.offset,
            "sort": request_dto.sort,
            "filters": {},
        }

        # Call repository pagination method
        entities, total = self.repository.buscar_productos_paginado(dto_dict)

        # Create pagination metadata
        metadata = PaginationMetadata.from_query(
            total_items=total,
            current_page=request_dto.page,
            per_page=request_dto.per_page,
        )

        # Convert entities to DTOs (if needed)
        items = entities  # Can be converted to DTOs in future

        return PaginatedResponseDTO(
            items=items,
            pagination=metadata,
            filters_applied={},
            sorting_applied={
                "field": request_dto.sort.split(":")[0] if request_dto.sort else None,
                "order": request_dto.sort.split(":")[1]
                if request_dto.sort and ":" in request_dto.sort
                else "asc",
            }
            if request_dto.sort
            else None,
        )
