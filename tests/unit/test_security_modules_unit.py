"""
Tests Unitarios - Security Modules (Cubren código real)
=====================================================

Tests que cubren código real de app.security.*
"""

import pytest
from app.security.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests de RateLimiter que cubren código real."""

    def test_rate_limiter_creates_with_defaults(self):
        """Crear RateLimiter con valores por defecto."""
        limiter = RateLimiter()

        assert limiter.rate_limit_per_client == 30
        assert limiter.rate_limit_global == 1000
        assert limiter.rate_limit_burst == 10

    def test_rate_limiter_with_custom_limits(self):
        """Crear RateLimiter con límites personalizados."""
        limiter = RateLimiter(
            rate_limit_per_client=10, rate_limit_global=500, rate_limit_burst=5
        )

        assert limiter.rate_limit_per_client == 10
        assert limiter.rate_limit_global == 500
        assert limiter.rate_limit_burst == 5

    def test_rate_limiter_is_rate_limit_enabled(self):
        """Verificar que rate_limiting está habilitado por defecto."""
        limiter = RateLimiter()

        assert limiter.rate_limit_enabled is True

    def test_rate_limiter_disabled(self):
        """Desactivar rate_limiting."""
        limiter = RateLimiter(rate_limit_enabled=False)

        assert limiter.rate_limit_enabled is False


class TestScrapingDetector:
    """Tests de ScrapingDetector que cubren código real."""

    def test_scraping_detector_creates_with_defaults(self):
        """Crear ScrapingDetector con valores por defecto."""
        from app.security.scraping_detector import ScrapingDetector

        detector = ScrapingDetector()

        assert detector.scraping_detection_enabled is True
        assert detector.ban_enabled is True

    def test_scraping_detector_blocked_user_agents(self):
        """Verificar user agents bloqueados."""
        from app.security.scraping_detector import ScrapingDetector

        detector = ScrapingDetector()

        assert "python-requests" in detector.blocked_user_agents
        assert "curl" in detector.blocked_user_agents
        assert "wget" in detector.blocked_user_agents

    def test_scraping_detector_ban_durations(self):
        """Verificar duraciones de ban."""
        from app.security.scraping_detector import ScrapingDetector

        detector = ScrapingDetector()

        assert detector.ban_duration_first_offense == 3600
        assert detector.ban_duration_second_offense == 86400


class TestUserAgentFilter:
    """Tests de UserAgentFilter que cubren código real."""

    def test_user_agent_filter_creates(self):
        """Crear UserAgentFilter."""
        from app.security.user_agent_filter import UserAgentFilter

        filter_obj = UserAgentFilter()

        assert filter_obj is not None

    def test_user_agent_filter_has_blocked_agents(self):
        """Verificar que tiene agentes bloqueados."""
        from app.security.user_agent_filter import UserAgentFilter

        filter_obj = UserAgentFilter()

        blocked = filter_obj.blocked_user_agents
        assert len(blocked) > 0
        assert "bot" in blocked or "crawler" in blocked


if __name__ == "__main__":
    pytest.main([__file__])
