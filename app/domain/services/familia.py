"""Domain service for Familia

Business logic layer for family statistics and aggregations.
."""

from typing import List, Dict
from app.application.dto.pagination import (
    PaginationRequestDTO,
    PaginatedResponseDTO,
    PaginationMetadata,
)
from app.domain.repositories.familia import FamiliaRepositoryInterface
from app.domain.entities.familia import FamiliaEntity


class FamiliaService:
    """
    Business logic service for Familia.

    This service contains business rules and aggregation logic
    for family statistics. It uses the repository interface for
    data access, maintaining dependency inversion and testability.
    """

    def __init__(self, repository: FamiliaRepositoryInterface):
        """
        Initialize service with repository.

        Args:
            repository: Familia repository implementation
        """
        self.repository = repository

    def get_all_familias(self) -> List[FamiliaEntity]:
        """
        Get all families with statistics

        Returns:
            List[FamiliaEntity]: All families with BC3 statistics
        """
        return self.repository.get_all()

    def get_familia_by_nombre(self, nombre: str) -> FamiliaEntity:
        """
        Get family by name with statistics

        Args:
            nombre: Family name

        Returns:
            FamiliaEntity: Family with statistics

        Raises:
            ValueError: If family not found
        """
        return self.repository.get_by_nombre(nombre)

    def get_statistics(self) -> Dict:
        """
        Get aggregate statistics across all families

        Returns:
            Dict: Aggregate statistics including total families, products, BC3 coverage
        """
        return self.repository.get_statistics()

    def get_bc3_coverage_leaderboard(self, limit: int = 5) -> List[FamiliaEntity]:
        """
        Get families with highest BC3 coverage

        Args:
            limit: Number of families to return

        Returns:
            List[FamiliaEntity]: Families sorted by BC3 coverage
        """
        familias = self.get_all_familias()

        # Sort by BC3 coverage percentage
        sorted_familias = sorted(
            familias, key=lambda f: f.get_bc3_coverage_percentage(), reverse=True
        )

        return sorted_familias[:limit]

    def buscar_familias_paginado(self, request_dto: PaginationRequestDTO) -> PaginatedResponseDTO:
        """Search families with pagination, sorting, and filtering.

        Args:
            request_dto: Pagination request with filters and sorting

        Returns:
            PaginatedResponseDTO: Families with pagination metadata
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
        entities: list[FamiliaEntity]
        total: int
        entities, total = self.repository.buscar_familias_paginado(dto_dict)

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
            filters_applied={
                key: value for key, value in dto_dict["filters"].items() if value is not None
            },
            sorting_applied={
                "field": request_dto.sort.split(":")[0] if request_dto.sort else None,
                "order": request_dto.sort.split(":")[1]
                if request_dto.sort and ":" in request_dto.sort
                else "asc",
            }
            if request_dto.sort
            else None,
        )
