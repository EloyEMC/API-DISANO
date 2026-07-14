"""Domain entities module

Domain entities represent core business objects that are independent
of infrastructure concerns like databases or external APIs.
."""

from app.domain.entities.producto import ProductoEntity

__all__ = ["ProductoEntity"]
