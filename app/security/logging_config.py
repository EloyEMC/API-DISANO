"""
Sistema de logging estructurado con loguru
Registra accesos, errores y eventos de seguridad
"""

import sys
from pathlib import Path
from loguru import logger
from app.config import get_settings

settings = get_settings()


def setup_logging():
    """
    Configura loguru para toda la aplicación.
    Llamar al inicio de main.py
    """
    # Remover handler default de stderr
    logger.remove()

    # Crear directorio de logs si no existe
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Formato de log detallado
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Console handler (salida estándar)
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # File handler (rotación y retención)
    logger.add(
        settings.log_file,
        format=log_format,
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",  # Comprimir logs antiguos
        backtrace=True,
        diagnose=True,
        encoding="utf-8"
    )

    # File handler específico para seguridad (security.log)
    if settings.security_log_enabled:
        security_log_path = log_file_path.parent / "security.log"
        logger.add(
            security_log_path,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level="WARNING",  # Solo WARNING y superior
            rotation="100 MB",
            retention="30 days",
            compression="zip"
        )

    logger.info(f"Logging configurado - Nivel: {settings.log_level}")
    logger.info(f"Log file: {settings.log_file}")
    if settings.security_log_enabled:
        logger.info(f"Security log: {security_log_path}")


def log_access_request(
    api_key: str,
    endpoint: str,
    method: str,
    client_ip: str,
    status_code: int
):
    """
    Registra un acceso a la API.

    Args:
        api_key: API key (primeros 8 caracteres)
        endpoint: Endpoint accedido
        method: Método HTTP
        client_ip: IP del cliente
        status_code: Código de respuesta HTTP
    """
    logger.bind(context="access").info(
        f"API_ACCESS | key={api_key} | {method} {endpoint} | "
        f"ip={client_ip} | status={status_code}"
    )


def log_security_event(
    event_type: str,
    details: str,
    client_ip: str = "unknown",
    api_key: str = "none"
):
    """
    Registra un evento de seguridad.

    Args:
        event_type: Tipo de evento (auth_failed, rate_limit, etc.)
        details: Detalles del evento
        client_ip: IP del cliente
        api_key: API key involucrada (si aplica)
    """
    logger.bind(context="security").warning(
        f"SECURITY_EVENT | type={event_type} | {details} | "
        f"ip={client_ip} | key={api_key}"
    )


# Exportar logger para uso en otros módulos
__all__ = ["logger", "setup_logging", "log_access_request", "log_security_event"]
