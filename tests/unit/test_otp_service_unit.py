"""
Tests Unitarios - Módulos Security (Sin Client Fixture)
=========================================================

Tests unitarios de módulos security que NO usan client fixture.
."""

import pytest
from app.security.otp_service import OTPService


class TestOTPServiceUnit:
    """Tests unitarios del servicio OTP sin client fixture."""

    def test_otp_generates_valid_code(self):
        ."""Verificar que OTP generado es válido (6 dígitos)."""
        otp_service = OTPService()
        email = "test@example.com"

        otp = otp_service.generate_otp(email)

        assert len(otp) == 6
        assert otp.isdigit()

    def test_otp_invalid_email_raises_error(self):
        """Verificar que email inválido lanza ValueError."""
        otp_service = OTPService()

        with pytest.raises(ValueError) as exc_info:
            otp_service.generate_otp("invalid-email")

        assert "Invalid email address" in str(exc_info.value)

    def test_otp_constants(self):
        """Verificar constantes del servicio OTP."""
        otp_service = OTPService()

        assert otp_service.otp_expiry_minutes == 10
        assert otp_service.max_attempts == 3
        assert otp_service.otp_length == 6

    def test_otp_status_returns_metadata(self):
        ."""Verificar que get_otp_status retorna metadatos correctos."""
        otp_service = OTPService()
        email = "test@example.com"

        otp = otp_service.generate_otp(email)
        status = otp_service.get_otp_status(email)

        assert status is not None
        assert status["email"] == email
        assert "attempts" in status
        assert "expiry" in status
        assert "verified" in status
        assert "expired" in status

    def test_otp_expired_fails_verification(self):
        """Verificar que OTP expirado falla verificación."""
        from datetime import datetime, timedelta

        otp_service = OTPService()
        email = "test@example.com"

        otp = otp_service.generate_otp(email)

        # Forzar expiración
        otp_service.otp_store[email]["expiry"] = datetime.now() - timedelta(minutes=1)

        is_valid, error = otp_service.verify_otp(email, otp)

        assert is_valid is False
        assert "expired" in error.lower()

    def test_otp_max_attempts_blocks_verification(self):
        """Verificar que máximo intentos bloquea verificación."""
        otp_service = OTPService()
        email = "test@example.com"

        otp = otp_service.generate_otp(email)

        # 3 intentos fallidos
        for _ in range(3):
            is_valid, _ = otp_service.verify_otp(email, "000000")

        # El 4to debería fallar porque el OTP fue eliminado
        is_valid, error = otp_service.verify_otp(email, otp)

        assert is_valid is False
        assert "No OTP found" in error or "Maximum attempts" in error


if __name__ == "__main__":
    pytest.main([__file__])
