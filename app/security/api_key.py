"""
Módulo de autenticación mediante API Keys
==========================================

Este módulo proporciona funciones para validar API Keys en las peticiones HTTP.
Implementa el patrón de Dependency Injection de FastAPI para proteger endpoints.

Uso típico:
    from fastapi import Depends
    from app.security.api_key import verify_api_key

    @router.get("/productos")
    async def get_productos(api_key: str = Depends(verify_api_key)):
        # api_key contiene los primeros 8 chars de la key validada
        pass

Funciones:
    verify_api_key: Dependency que valida X-API-Key header
"""

from fastapi import Header, HTTPException, status
from typing import Optional
from app.config import get_settings
from app.security.logging_config import logger, log_security_event

settings = get_settings()


async def verify_api_key(
    x_api_key: Optional[str] = Header(
        None,
        alias=settings.api_key_header,
        description=f"API Key para autenticación. Header: {settings.api_key_header}"
    )
) -> str:
    """
    Dependency que verifica la API Key en el header.

    Esta función se usa como dependency de FastAPI para proteger endpoints.
    Si no se proporciona API key o es inválida, lanza HTTPException 401.

    Args:
        x_api_key: API Key del header X-API-Key (inyectada por FastAPI)

    Returns:
        str: Los primeros 8 caracteres de la API Key validada (para logging)

    Raises:
        HTTPException 401: Si no hay API key o es inválida

    Ejemplo:
        @router.get("/")
        async def endpoint(api_key: str = Depends(verify_api_key)):
            # api_key = "abc12345..." (primeros 8 caracteres)
            return {"message": "Autorizado"}
    """
    # Verificar si se proporcionó API key
    if not x_api_key:
        logger.warning("Intento de acceso sin API key")
        log_security_event(
            event_type="auth_failed",
            details="No API key provided",
            api_key="none"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key requerida. Proporciona el header X-API-Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verificar si la API key es válida
    if x_api_key not in settings.api_keys:
        # Solo mostrar primeros 8 caracteres por seguridad
        key_preview = f"{x_api_key[:8]}..." if len(x_api_key) > 8 else x_api_key
        logger.warning(f"Intento de acceso con API key inválida: {key_preview}")
        log_security_event(
            event_type="auth_failed",
            details=f"Invalid API key: {key_preview}",
            api_key=key_preview
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # API key válida - loggear acceso y retornar preview
    key_preview = f"{x_api_key[:8]}..." if len(x_api_key) > 8 else x_api_key
    logger.info(f"API Key validada correctamente: {key_preview}")

    return key_preview
