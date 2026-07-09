"""
Detector de Patrones de Scraping
=================================

Este módulo implementa detección heurística de comportamientos de scraping.
Analiza patrones de peticiones para identificar scrapers que no son
bloqueados por el filtro básico de User-Agent.

Patrones detectados:
    1. Peticiones secuenciales de productos (1, 2, 3, 4...)
    2. Múltiples peticiones sin cambiar límites de paginación
    3. Timing perfecto (peticiones a intervalos regulares imposibles para humanos)
    4. Peticiones sin referer
    5. Mismos headers en todas las peticiones
    6. Acceso a endpoints de honeypot

Para producción se recomienda usar Redis para almacenar estadísticas
de peticiones y patrones.

Uso:
    from fastapi import Request
    from app.security.scraping_detector import ScrapingDetector

    detector = ScrapingDetector()

    @app.middleware("http")
    async def detect_scraping(request: Request, call_next):
        if detector.is_suspicious_request(request):
            raise HTTPException(403, "Suspicious activity detected")
        return await call_next(request)
"""

from fastapi import Request
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
from app.config import get_settings
from app.security.logging_config import logger, log_security_event

settings = get_settings()


class ScrapingDetector:
    """
    Detector de patrones de scraping usando análisis heurístico.

    Mantiene estadísticas en memoria de peticiones por IP/API key.
    Para producción con múltiples workers, usar Redis en lugar de memoria.

    Atributos:
        request_history: Historial de peticiones por identificador
        pattern_counts: Contador de patrones sospechosos por identificador
        honeypot_accesses: IPs que accedieron a honeypots

    Ejemplo:
        detector = ScrapingDetector()

        # Analizar petición
        if detector.is_suspicious_request(request):
            logger.warning("Posible scraper detectado")
    """

    def __init__(self):
        """Inicializa el detector con estructuras de datos vacías."""
        # Historial de peticiones: {identifier: [(timestamp, endpoint), ...]}
        self.request_history: Dict[str, List[tuple]] = defaultdict(list)

        # Contadores de patrones sospechosos: {identifier: {pattern: count}}
        self.pattern_counts: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        # IPs bloqueadas temporalmente: {ip: unban_timestamp}
        self.banned_ips: Dict[str, float] = {}

        # Honeypot accesses: {ip: access_count}
        self.honeypot_accesses: Dict[str, int] = {}

        # Limpiar historiales antiguos periódicamente
        self._cleanup_old_entries()

    def _get_identifier(self, request: Request) -> str:
        """
        Genera un identificador único para el cliente.

        Prioriza API key sobre IP address para tracking.

        Args:
            request: Objeto Request de FastAPI

        Returns:
            str: Identificador del cliente
        """
        api_key = request.headers.get(settings.api_key_header)
        if api_key:
            # Usar API key (hash por seguridad)
            return f"apikey:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        else:
            # Fallback a IP
            return f"ip:{request.client.host if request.client else 'unknown'}"

    def _cleanup_old_entries(self):
        """
        Limpia entradas del historial más antiguas que 1 hora.

        Se llama automáticamente en cada análisis para evitar
        consumo excesivo de memoria.
        """
        cutoff_time = datetime.now() - timedelta(hours=1)

        for identifier in list(self.request_history.keys()):
            # Filtrar peticiones recientes
            self.request_history[identifier] = [
                (ts, endpoint) for ts, endpoint in self.request_history[identifier]
                if ts > cutoff_time
            ]

            # Eliminar identificador si no hay peticiones recientes
            if not self.request_history[identifier]:
                del self.request_history[identifier]

    def _is_timing_perfect(self, request_history: List[tuple]) -> bool:
        """
        Detecta si las peticiones tienen timing perfecto (imposible para humanos).

        Los humanos no pueden hacer peticiones a intervalos perfectos
        de 100ms o menos. Los scrapers sí.

        Args:
            request_history: Lista de (timestamp, endpoint)

        Returns:
            bool: True si el timing es sospechosamente perfecto
        """
        if len(request_history) < 10:
            return False

        # Calcular intervalos entre peticiones
        intervals = []
        for i in range(1, min(len(request_history), 20)):
            interval = (request_history[i][0] - request_history[i-1][0]).total_seconds()
            intervals.append(interval)

        # Si todos los intervalos son < 200ms y muy consistentes
        if len(intervals) >= 10:
            avg_interval = sum(intervals) / len(intervals)
            if avg_interval < 0.2:  # Menos de 200ms promedio
                # Calcular desviación estándar
                variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
                std_dev = variance ** 0.5
                # Si desviación estándar es baja → timing perfecto (scraper)
                if std_dev < 0.05:
                    return True

        return False

    def _is_sequential_access(self, request_history: List[tuple]) -> bool:
        """
        Detecta acceso secuencial a productos (1, 2, 3, 4...).

        Los scrapers suelen acceder productos secuencialmente por código.
        Los humanos suelen buscar productos específicos o usar filtros.

        Args:
            request_history: Lista de (timestamp, endpoint)

        Returns:
            bool: True si detecta patrón secuencial sospechoso
        """
        if len(request_history) < 20:
            return False

        # Extraer códigos de producto de endpoints
        # Ejemplo: /v1/internal/products/11253300
        import re
        product_codes = []
        pattern = r'/products/(\d+)'

        for _, endpoint in request_history[-50:]:  # Últimas 50 peticiones
            match = re.search(pattern, endpoint)
            if match:
                try:
                    code = int(match.group(1))
                    product_codes.append(code)
                except ValueError:
                    pass

        # Verificar si los códigos son secuenciales
        if len(product_codes) >= 20:
            # Calcular diferencias entre códigos consecutivos
            differences = [
                product_codes[i+1] - product_codes[i]
                for i in range(len(product_codes) - 1)
            ]

            # Si la mayoría de diferencias son pequeñas (0-100), es secuencial
            small_diffs = sum(1 for d in differences if 0 <= d <= 100)
            if small_diffs / len(differences) > 0.8:  # 80% secuenciales
                return True

        return False

    def _has_no_referer(self, request: Request) -> bool:
        """
        Verifica si la petición tiene referer.

        Las peticiones directas desde scripts no suelen tener referer.
        Las peticiones desde navegadores legítimos sí tienen.

        Args:
            request: Objeto Request de FastAPI

        Returns:
            bool: True si no tiene referer (suspicioso)
        """
        referer = request.headers.get("referer", "")
        return not referer

    def analyze_request(self, request: Request) -> dict:
        """
        Analiza una petición y calcula puntuación de sospecha.

        Evalúa múltiples heurísticas y retorna una puntuación
        de 0 a 100, donde 100 es máxima sospecha de scraping.

        Args:
            request: Objeto Request de FastAPI

        Returns:
            dict: Información del análisis con campos:
                - score: Puntuación de sospecha (0-100)
                - is_suspicious: True si score > 70
                - reasons: Lista de razones detectadas
                - patterns: Patrones encontrados

        Ejemplo:
            {
                "score": 85,
                "is_suspicious": True,
                "reasons": ["Sequential access detected", "No referer"],
                "patterns": {"sequential_access": 45, "no_referer": 10}
            }
        """
        identifier = self._get_identifier(request)
        current_time = datetime.now()

        # Registrar petición en historial
        endpoint = request.url.path
        self.request_history[identifier].append((current_time, endpoint))

        # Limpiar entradas antiguas
        self._cleanup_old_entries()

        # Analizar patrones
        history = self.request_history[identifier]
        score = 0
        reasons = []
        patterns = {}

        # 1. Timing perfecto (máximo 30 puntos)
        if self._is_timing_perfect(history):
            score += 30
            reasons.append("Perfect timing detected (bot-like)")
            patterns["perfect_timing"] = 30

        # 2. Acceso secuencial (máximo 40 puntos)
        if self._is_sequential_access(history):
            score += 40
            reasons.append("Sequential product access detected")
            patterns["sequential_access"] = 40

        # 3. Sin referer (máximo 10 puntos)
        if self._has_no_referer(request):
            score += 10
            reasons.append("No referer header")
            patterns["no_referer"] = 10

        # 4. Demasiadas peticiones en poco tiempo (máximo 20 puntos)
        recent_count = len([ts for ts, _ in history if (current_time - ts).total_seconds() < 60])
        if recent_count > 50:
            score += 20
            reasons.append(f"Too many requests: {recent_count}/minute")
            patterns["high_frequency"] = 20

        # Actualizar contadores
        for pattern, value in patterns.items():
            self.pattern_counts[identifier][pattern] += value

        # Determinar si es sospechoso (umbral: 70 puntos)
        is_suspicious = score >= 70

        if is_suspicious:
            logger.warning(
                f"Scraping detectado: {identifier} - Score: {score} - "
                f"Razones: {', '.join(reasons)}"
            )
            log_security_event(
                event_type="scraping_detected",
                details=f"Score: {score} - {', '.join(reasons)}",
                api_key=identifier.split(":")[1] if "apikey:" in identifier else "none"
            )

        return {
            "score": score,
            "is_suspicious": is_suspicious,
            "reasons": reasons,
            "patterns": patterns
        }

    def is_suspicious_request(self, request: Request) -> bool:
        """
        Verifica rápidamente si una petición es sospechosa.

        Versión simplificada de analyze_request() para uso en middleware.

        Args:
            request: Objeto Request de FastAPI

        Returns:
            bool: True si la petición parece ser de un scraper
        """
        if not settings.scraping_detection_enabled:
            return False

        # Verificar si IP está baneada
        client_ip = request.client.host if request.client else "unknown"
        if client_ip in self.banned_ips:
            # Verificar si ban ha expirado
            if datetime.now().timestamp() > self.banned_ips[client_ip]:
                del self.banned_ips[client_ip]
            else:
                return True

        # Análisis completo
        analysis = self.analyze_request(request)

        # Si es muy sospechoso, banear IP temporalmente
        if analysis["score"] >= 90:
            ban_duration = settings.ban_duration_first_offense
            self.banned_ips[client_ip] = datetime.now().timestamp() + ban_duration
            logger.warning(f"IP baneada temporalmente: {client_ip} - Duración: {ban_duration}s")

        return analysis["is_suspicious"]

    def is_honeypot_access(self, request: Request) -> bool:
        """
        Verifica si la petición accede a un endpoint honeypot.

        Los honeypots son endpoints falsos que solo los scrapers
        explorando la API encontrarían.

        Args:
            request: Objeto Request de FastAPI

        Returns:
            bool: True si accede a honeypot

        Endpoints honeypot:
            - /api/sitemap.xml
            - /api/products/export
            - /api/all-products
            - /sitemap.xml
        """
        honeypot_paths = [
            "/api/sitemap.xml",
            "/api/products/export",
            "/api/all-products",
            "/sitemap.xml",
            "/api/.well-known/",
        ]

        if any(request.url.path.startswith(path) for path in honeypot_paths):
            client_ip = request.client.host if request.client else "unknown"
            self.honeypot_accesses[client_ip] = self.honeypot_accesses.get(client_ip, 0) + 1

            logger.warning(f"HONEYPOT accedido: {request.url.path} desde {client_ip}")
            log_security_event(
                event_type="honeypot_access",
                details=f"Honeypot: {request.url.path}",
                api_key="none"
            )

            # Banear permanentemente tras 2 accesos a honeypot
            if self.honeypot_accesses[client_ip] >= 2:
                self.banned_ips[client_ip] = float('inf')  # Ban permanente
                logger.error(f"IP baneada permanentemente por honeypot: {client_ip}")

            return True

        return False

    def get_banned_ips(self) -> List[str]:
        """
        Retorna lista de IPs baneadas actualmente.

        Returns:
            list[str]: Lista de IPs baneadas

        Nota: Incluye tanto bans temporales como permanentes
        """
        current_time = datetime.now().timestamp()

        # Filtrar bans expirados
        active_bans = [
            ip for ip, expiry in self.banned_ips.items()
            if expiry > current_time or expiry == float('inf')
        ]

        return active_bans

    def unban_ip(self, ip: str) -> bool:
        """
        Elimina el ban de una IP específica.

        Args:
            ip: Dirección IP a desbloquear

        Returns:
            bool: True si la IP estaba baneada y fue desbloqueada
        """
        if ip in self.banned_ips:
            del self.banned_ips[ip]
            logger.info(f"IP desbloqueada: {ip}")
            return True
        return False


# Instancia global del detector
detector = ScrapingDetector()
