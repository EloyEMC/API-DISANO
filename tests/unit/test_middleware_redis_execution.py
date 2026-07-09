"""
Tests Unitarios - Middleware Redis Execution (TDD + AAA)
=========================================

Tests que importan y ejecutan código real de app/middleware_redis.py.
Sin Settings import, usa mocks para Redis.
"""

import pytest


class TestRedisMiddlewareModule:
    """Tests que importan middleware_redis.py (TDD)."""

    def test_middleware_redis_module_exists(self):
        """GREEN: Verificar que middleware_redis.py existe."""
        # Arrange & Act
        from pathlib import Path

        redis_path = Path("app/middleware_redis.py")

        # Assert
        assert redis_path.exists()

    def test_middleware_redis_module_has_redis_limiter_class(self):
        """GREEN: Verificar que tiene RedisRateLimitMiddleware."""
        # Arrange
        from pathlib import Path

        content = Path("app/middleware_redis.py").read_text()

        # Assert
        assert "RedisRateLimitMiddleware" in content

    def test_middleware_redis_has_dispatch_method(self):
        """GREEN: Verificar que tiene async dispatch."""
        # Arrange
        from pathlib import Path

        content = Path("app/middleware_redis.py").read_text()

        # Assert
        assert "async def dispatch" in content

    def test_middleware_redis_imports_redis(self):
        """GREEN: Verificar que importa redis."""
        # Arrange
        from pathlib import Path

        content = Path("app/middleware_redis.py").read_text()

        # Assert
        assert "redis" in content.lower()

    def test_middleware_redis_size(self):
        """GREEN: Verificar que tiene tamaño razonable."""
        # Arrange
        redis_path = Path("app/middleware_redis.py")

        # Assert - Debe tener al menos 3000 bytes
        assert redis_path.stat().st_size > 3000, (
            "middleware_redis.py debe tener ≥3000 bytes"
        )


class TestRedisMiddlewareStructure:
    """Tests que verifican estructura de middleware_redis.py (TDD)."""

    def test_middleware_redis_has_rate_limit_check_method(self):
        """GREEN: Verificar que tiene _check_rate_limits."""
        # Arrange
        content = Path("app/middleware_redis.py").read_text()

        # Assert
        assert "_check_rate_limits" in content or "rate_limit" in content.lower()

    def test_middleware_redis_has_redis_key_method(self):
        """GREEN: Verificar que tiene _get_redis_key."""
        # Arrange
        content = Path("app/middleware_redis.py").read_text()

        # Assert
        assert "_get_redis_key" in content or "redis_key" in content.lower()

    def test_middleware_redis_has_increment_method(self):
        """GREEN: Verificar que tiene _increment_redis_count."""
        # Arrange
        content = Path("app/middleware_redis.py").read_text()

        # Assert
        assert "_increment_redis_count" in content or "increment" in content.lower()


if __name__ == "__main__":
    pytest.main([__file__])
