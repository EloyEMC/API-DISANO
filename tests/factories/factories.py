"""
Factories para tests de API-DISANO
=========================================

Factories pytest para crear datos de prueba siguiendo BC3-Suite patterns.
"""

import random
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class ProductoFactory:
    """Factory para crear productos de prueba."""

    @staticmethod
    def base() -> dict:
        """
        Producto base con campos mínimos.

        Returns:
            dict: Producto base
        """
        return {
            "codigo": f"TEST-{random.randint(100000, 999999)}",
            "descripcion": f"Test producto {random.randint(1000, 9999)}",
            "pvp": round(random.uniform(5.0, 500.0), 2),
            "marca": random.choice(["Disano", "Fosnova"]),
            "familia_web": random.choice(
                [
                    "Iluminación",
                    "Conmutadores",
                    "Instalación",
                    "Cables",
                    "Materiales",
                    "Herramientas",
                ]
            ),
            "descontinuado": False,
        }

    @staticmethod
    def with_bc3() -> dict:
        """
        Producto con campos BC3 llenos.

        Returns:
            dict: Producto con BC3
        """
        producto = ProductoFactory.base()
        producto.update(
            {
                "bc3_descripcion_corta": f"Test BC3 {producto['codigo']}",
                "bc3_descripcion_larga": f"Descripción larga BC3 de {producto['codigo']}",
                "bc3_product_type": random.choice(
                    ["Lámpara", "Conmutador", "Cable", "Material"]
                ),
                "bc3_descripcion_completa": f"BC3 completo: {producto['descripcion']}",
                "bc3_processed_at": datetime.now().isoformat(),
                "url_imagen": f"https://example.com/images/{producto['codigo']}.jpg",
            }
        )
        return producto

    @staticmethod
    def with_imagen() -> dict:
        """
        Producto con imagen.

        Returns:
            dict: Producto con imagen
        """
        producto = ProductoFactory.base()
        producto["url_imagen"] = f"https://example.com/images/{producto['codigo']}.jpg"
        producto["img_url"] = producto["url_imagen"]
        return producto

    @staticmethod
    def descontinuado() -> dict:
        """
        Producto descontinuado.

        Returns:
            dict: Producto descontinuado
        """
        producto = ProductoFactory.base()
        producto["descontinuado"] = True
        return producto

    @staticmethod
    def create_batch(count: int = 10, **kwargs) -> list[dict]:
        """
        Crear múltiples productos de prueba.

        Args:
            count: Número de productos a crear
            **kwargs: Atributos adicionales

        Returns:
            list[dict]: Lista de productos

        Example:
            productos = ProductoFactory.create_batch(5, marca="Disano")
            assert all(p["marca"] == "Disano" for p in productos)
        """
        productos = []
        for _ in range(count):
            producto = ProductoFactory.base()
            productos.append({**producto, **kwargs})
        return productos


@dataclass
class OTPFactory:
    """Factory para crear datos OTP de prueba."""

    @staticmethod
    def valid() -> dict:
        """
        OTP válido con metadatos completos.

        Returns:
            dict: OTP con metadatos
        """
        return {
            "code": "123456",
            "email": "test@example.com",
            "expiry": datetime.now() + timedelta(minutes=10),
            "attempts": 0,
            "verified": False,
        }

    @staticmethod
    def expired() -> dict:
        """
        OTP expirado.

        Returns:
            dict: OTP expirado
        """
        return {
            "code": "123456",
            "email": "test@example.com",
            "expiry": datetime.now() - timedelta(minutes=1),  # Expired hace 1 minuto
            "attempts": 0,
            "verified": False,
        }

    @staticmethod
    def max_attempts_reached() -> dict:
        """
        OTP con máximo de intentos alcanzados.

        Returns:
            dict: OTP bloqueado
        """
        return {
            "code": "123456",
            "email": "test@example.com",
            "expiry": datetime.now() + timedelta(minutes=10),
            "attempts": 3,
            "verified": False,
        }


@dataclass
class RequestFactory:
    """Factory para crear requests HTTP de prueba."""

    @staticmethod
    def create_producto_get_request(codigo: str | None = None, **kwargs) -> dict:
        """
        Request GET para producto.

        Args:
            codigo: Código del producto (opcional)
            **kwargs: Parámetros adicionales (limit, marca, etc.)

        Returns:
            dict: Request simulado

        Example:
            request = RequestFactory.create_producto_get_request(
                codigo="33036139",
                limit=5
            )
            response = client.get("/api/productos/", params=request)
        """
        base_params = {
            "skip": 0,
            "limit": 10,
        }
        base_params.update(kwargs)

        path = "/api/productos/" if not codigo else f"/api/productos/{codigo}"
        return {
            "method": "GET",
            "path": path,
            "params": base_params if not codigo else None,
            "body": None,
            "headers": None,
        }

    @staticmethod
    def create_admin_create_request(**kwargs) -> dict:
        """
        Request POST para crear producto (admin).

        Returns:
            dict: Request simulado

        Example:
            request = RequestFactory.create_admin_create_request(
                codigo="12345678",
                descripcion="Test admin",
                pvp=19.99
            )
            response = client.post("/api/admin/productos", json=request["body"], headers=admin_headers)
        """
        producto = ProductoFactory.with_bc3()
        request = {
            "method": "POST",
            "path": "/api/admin/productos",
            "params": None,
            "body": producto,
            "headers": None,
        }
        return request


@dataclass
class UserFactory:
    """Factory para crear usuarios de prueba."""

    @staticmethod
    def admin() -> dict:
        """
        Usuario admin de prueba.

        Returns:
            dict: Usuario admin
        """
        return {
            "id": "admin-user-1",
            "email": "admin@example.com",
            "role": "admin",
            "rol_en_zona": None,
            "zona_id": None,
        }

    @staticmethod
    def sales() -> dict:
        """
        Usuario sales de prueba.

        Returns:
            dict: Usuario sales
        """
        return {
            "id": "sales-user-1",
            "email": "sales@example.com",
            "role": "sales",
            "rol_en_zona": None,
            "zona_id": None,
        }

    @staticmethod
    def coordinator() -> dict:
        """
        Usuario coordinador de prueba.

        Returns:
            dict: Usuario coordinador
        """
        return {
            "id": "coordinador-user-1",
            "email": "coordinador@example.com",
            "role": "sales",
            "rol_en_zona": "coordinador",
            "zona_id": "zona-1",
        }
