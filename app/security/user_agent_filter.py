"""
Filtro de User-Agent anti-scraping
===================================

Este módulo implementa filtrado de User-Agents para bloquear scrapers conocidos.
Es la primera línea de defensa contra scraping automatizado básico.

User-Agents bloqueados por defecto:
    - python-requests: Cliente HTTP Python (scrapers más comunes)
    - curl: Herramienta de línea de comandos
    - wget: Herramienta de descarga
    - scraper: Generic scrapers
    - crawler: Web crawlers
    - bot: Generic bots
    - spider: Web spiders
    - headless: Navegadores headless (Selenium, Puppeteer)
    - phantom: PhantomJS headless browser
    - selenium: Selenium automation

Nota: Los navegadores legítimos envían User-Agentes como:
    - Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0
    - Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36

Uso:
    from fastapi import Request
    from app.security.user_agent_filter import is_user_agent_allowed

    @app.middleware("http")
    async def filter_user_agent(request: Request, call_next):
        if not is_user_agent_allowed(request):
            raise HTTPException(403, "User-Agent not allowed")
        return await call_next(request)
"""

from fastapi import Request
from app.config import get_settings
from app.security.logging_config import logger, log_security_event

settings = get_settings()


def is_user_agent_allowed(request: Request) -> bool:
    """
    Verifica si el User-Agent de la petición está permitido.

    Comprueba si el User-Agent coincide con alguno de los patrones bloqueados.
    La comparación es case-insensitive.

    Args:
        request: Objeto Request de FastAPI

    Returns:
        bool: True si está permitido, False si está bloqueado

    Ejemplo:
        # User-Agent bloqueado
        request.headers["user-agent"] = "python-requests/2.28.0"
        # → Returns False

        # User-Agent permitido
        request.headers["user-agent"] = "Mozilla/5.0 (Chrome)"
        # → Returns True
    """
    user_agent = request.headers.get("user-agent", "")

    # Si no hay user-agent, bloquear (suspiccioso)
    if not user_agent:
        logger.warning(f"Petición sin User-Agent desde {request.client.host}")
        log_security_event(
            event_type="blocked_user_agent",
            details="No User-Agent provided",
            api_key="none"
        )
        return False

    # Convertir a minúsculas para comparación case-insensitive
    user_agent_lower = user_agent.lower()

    # Verificar contra la lista de User-Agents bloqueados
    for blocked_pattern in settings.blocked_user_agents:
        if blocked_pattern.lower() in user_agent_lower:
            logger.warning(
                f"User-Agent bloqueado: {user_agent} "
                f"(contiene '{blocked_pattern}') desde {request.client.host}"
            )
            log_security_event(
                event_type="blocked_user_agent",
                details=f"Blocked pattern: {blocked_pattern}",
                api_key="none"
            )
            return False

    # User-Agent permitido
    logger.debug(f"User-Agent permitido: {user_agent}")
    return True


def get_user_agent_info(request: Request) -> dict:
    """
    Extrae información del User-Agent para logging/analítica.

    Args:
        request: Objeto Request de FastAPI

    Returns:
        dict: Información del User-Agent con campos:
            - user_agent: User-Agent completo
            - is_browser: True si parece un navegador legítimo
            - is_bot: True si parece un bot/crawler
            - type: Tipo de cliente (browser, bot, scraper, unknown)

    Ejemplo:
        {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/120.0.0.0",
            "is_browser": True,
            "is_bot": False,
            "type": "browser"
        }
    """
    user_agent = request.headers.get("user-agent", "")

    info = {
        "user_agent": user_agent,
        "is_browser": False,
        "is_bot": False,
        "type": "unknown"
    }

    if not user_agent:
        return info

    user_agent_lower = user_agent.lower()

    # Detectar navegadores legítimos
    browser_patterns = ["mozilla", "chrome", "safari", "firefox", "edge", "opera"]
    if any(pattern in user_agent_lower for pattern in browser_patterns):
        info["is_browser"] = True
        info["type"] = "browser"

    # Detectar bots conocidos
    bot_patterns = ["bot", "crawler", "spider", "googlebot", "bingbot"]
    if any(pattern in user_agent_lower for pattern in bot_patterns):
        info["is_bot"] = True
        info["type"] = "bot"

    # Detectar scrapers
    scraper_patterns = ["python-requests", "curl", "wget", "scrape"]
    if any(pattern in user_agent_lower for pattern in scraper_patterns):
        info["type"] = "scraper"

    return info
