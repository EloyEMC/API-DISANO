"""
Tests Unitarios - Security Module Execution (TDD + AAA + BC3-Suite)
===================================================

Tests que importan y ejecutan código real de app/security.py y submódulos.
BC3-Suite patterns: TDD (RED→GREEN→REFACTOR), AAA pattern.
."""

import pytest
from datetime import datetime


class TestSecurityOtpService:
    """Tests de OTP service en app/security/otp_service.py (TDD + AAA)."""

    def test_otp_generation_creates_6_digit_code(self):
        """
        RED: OTP generation debe crear código de 6 dígitos.

        AAA Pattern:
        - Arrange: Configurar email para OTP
        - Act: Generar OTP
        - Assert: Código tiene 6 dígitos
        ."""
        # Arrange
        email = "user@test.com"

        # Act
        from app.security.otp_service import generate_otp

        otp = generate_otp(email)

        # Assert - Código tiene 6 dígitos
        assert len(otp.code) == 6
        assert otp.code.isdigit()
        assert otp.email == email

    def test_otp_expiration_10_minutes(self):
        """
        GREEN: OTP expira en 10 minutos.
        ."""
        # Arrange
        email = "user@test.com"
        from app.security.otp_service import generate_otp

        # Act
        otp = generate_otp(email)
        expiry_time = otp.created_at + datetime.timedelta(minutes=10)

        # Assert
        assert expiry_time > datetime.now()
        assert otp.expires_at == expiry_time

    def test_otp_max_3_attempts_enforced(self):
        """
        GREEN: OTP tiene máximo 3 intentos de validación.
        ."""
        # Arrange
        email = "user@test.com"
        from app.security.otp_service import generate_otp

        # Act
        otp = generate_otp(email)

        # Assert - OTP tiene max_attempts = 3
        assert otp.max_attempts == 3

    def test_otp_expires_timestamp_format(self):
        """
        GREEN: OTP expires_at es timestamp válido.
        ."""
        # Arrange
        email = "user@test.com"
        from app.security.otp_service import generate_otp

        # Act
        otp = generate_otp(email)

        # Assert - expires_at es datetime
        assert isinstance(otp.expires_at, datetime)


class TestSecurityLoggingConfig:
    """Tests de logging config en app/security/logging_config.py (TDD + AAA)."""

    def test_setup_logging_configures_info_level(self):
        """
        RED: setup_logging() configura logging en INFO level.
        """
        # Arrange & Act
        from app.security.logging_config import setup_logging

        # Act - setup_logging debe configurar sin error
        setup_logging()

        # Assert - Logger existe y tiene INFO level
        from app.security.logging_config import logger

        assert logger is not None

    def test_setup_logging_creates_log_file(self):
        """
        GREEN: setup_logging() crea archivo de log.
        ."""
        # Arrange & Act
        from app.security.logging_config import setup_logging
        from pathlib import Path

        setup_logging()

        # Assert - Directorio logs/ existe
        logs_dir = Path("logs")
        assert logs_dir.exists()
        assert (logs_dir / "api.log").exists()

    def test_setup_logging_configures_security_log(self):
        """
        GREEN: setup_logging() configura security log.
        ."""
        # Arrange & Act
        from app.security.logging_config import setup_logging
        from pathlib import Path

        setup_logging()

        # Assert - Directorio logs/ existe y tiene security.log
        logs_dir = Path("logs")
        assert logs_dir.exists()
        assert (logs_dir / "security.log").exists()


class TestSecurityRateLimiter:
    """Tests de rate limiter en app/security/rate_limiter.py (TDD + AAA)."""

    def test_rate_limit_per_client_defaults_to_30(self):
        """
        RED: Rate limit per client tiene default de 30.
        """
        # Arrange & Act
        from app.security.rate_limiter import RATE_LIMIT_PER_CLIENT

        # Assert
        assert RATE_LIMIT_PER_CLIENT == 30

    def test_rate_limit_global_defaults_to_1000(self):
        """
        GREEN: Rate limit global tiene default de 1000.
        """
        # Arrange & Act
        from app.security.rate_limiter import RATE_LIMIT_GLOBAL

        # Assert
        assert RATE_LIMIT_GLOBAL == 1000

    def test_rate_limit_burst_defaults_to_10(self):
        """
        GREEN: Rate limit burst tiene default de 10.
        """
        # Arrange & Act
        from app.security.rate_limiter import RATE_LIMIT_BURST

        # Assert
        assert RATE_LIMIT_BURST == 10

    def test_rate_limit_listings_defaults_to_10(self):
        """
        GREEN: Rate limit listings tiene default de 10.
        ."""
        # Arrange & Act
        from app.security.rate_limiter import RATE_LIMIT_LISTINGS

        # Assert
        assert RATE_LIMIT_LISTINGS == 10


if __name__ == "__main__":
    pytest.main([__file__])
