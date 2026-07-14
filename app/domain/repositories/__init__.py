"""Repository interfaces module

Defines abstract interfaces for data access - dependency inversion principle.
Implementations are in infrastructure layer.
."""

from app.domain.repositories.producto import ProductoRepositoryInterface

__all__ = ["ProductoRepositoryInterface"]
