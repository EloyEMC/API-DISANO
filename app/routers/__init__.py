"""Routers Package.

This package provides backward compatibility for imports from app.routers.
The actual routers are located in app.interfaces.http.
"""

from app.interfaces.http import productos as productos_http
from app.interfaces.http import familias as familias_http
from app.interfaces.http import bc3 as bc3_http

# Expose the routers for backward compatibility
productos = productos_http
familias = familias_http
bc3 = bc3_http

__all__ = ["productos", "familias", "bc3"]
