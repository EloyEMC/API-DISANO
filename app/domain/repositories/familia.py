"""Repository interface for Familia

Abstract repository interface following Domain-Driven Design principles.
."""

from abc import ABC, abstractmethod
from typing import List, Dict
from app.domain.entities.familia import FamiliaEntity


class FamiliaRepositoryInterface(ABC):
    """Abstract repository for Familia operations."""

    @abstractmethod
    def get_all(self) -> List[FamiliaEntity]:
        """
        Get all families with statistics

        Returns:
            List[FamiliaEntity]: All families with BC3 statistics
        ."""
        pass

    @abstractmethod
    def get_by_nombre(self, nombre: str) -> FamiliaEntity:
        """
        Get family by name

        Args:
            nombre: Family name

        Returns:
            FamiliaEntity: Family with statistics

        Raises:
            Exception: If family not found
        ."""
        pass

    @abstractmethod
    def get_statistics(self) -> Dict:
        """
        Get aggregate statistics across all families

        Returns:
            Dict: Aggregate statistics including total families, products, BC3 coverage
        ."""
        pass

    @abstractmethod
    def buscar_familias_paginado(self, dto: dict) -> tuple[list[FamiliaEntity], int]:
        """Search families with pagination, sorting, and filtering

                Args:
                    dto: Complete pagination request DTO with filters and sorting

                Returns:
                    tuple[list[FamiliaEntity], int]:
        - List of entities for current page
        - Total count of matching items
        ."""
        pass
