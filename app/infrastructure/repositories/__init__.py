"""Infrastructure repositories module

SQLAlchemy implementations of domain repository interfaces.
"""

from app.infrastructure.repositories.producto import SQLAlchemyProductoRepository

__all__ = ["SQLAlchemyProductoRepository"]
