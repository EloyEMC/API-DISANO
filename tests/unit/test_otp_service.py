"""
Tests del Servicio OTP
========================

Tests para verificar el funcionamiento del servicio 2FA/OTP.
."""

import pytest
from datetime import datetime, timedelta
from app.security.otp_service import OTPService


class TestOTPServiceGeneration:
    """Tests para la generación de OTP."""

    def test_generate_otp_valid_email(self):
        ."""Verificar que se genera un OTP para email válido."""
        otp_service = OTPService()
        otp = otp_service.generate_otp("admin@example.com")

        # Verificar que es un string de 6 dígitos
        assert isinstance(otp, str)
        assert len(otp) == 6
        assert otp.isdigit()

    def test_generate_otp_invalid_email(self):
        """Verificar que lanza error para email inválido."""
        otp_service = OTPService()

        with pytest.raises(ValueError) as exc_info:
            otp_service.generate_otp("invalid-email")

        assert "Invalid email address" in str(exc_info.value)

    def test_generate_otp_empty_email(self):
        """Verificar que lanza error para email vacío."""
        otp_service = OTPService()

        with pytest.raises(ValueError) as exc_info:
            otp_service.generate_otp("")

        assert "Invalid email address" in str(exc_info.value)

    def test_generate_otp_stores_metadata(self):
        """Verificar que el OTP guarda metadatos correctas."""
        otp_service = OTPService()
        email = "admin@example.com"

        otp_service.generate_otp(email)

        otp_data = otp_service.otp_store.get(email)
        assert otp_data is not None
        assert otp_data["code"] in otp_service.otp_store[email]
        assert otp_data["attempts"] == 0
        assert otp_data["verified"] is False
        assert otp_data["expiry"] > datetime.now()


class TestOTPServiceVerification:
    """Tests para la verificación de OTP."""

    def test_verify_otp_valid(self):
        ."""Verificar que un OTP válido se verifica correctamente."""
        otp_service = OTPService()
        email = "admin@example.com"

        otp = otp_service.generate_otp(email)
        is_valid, error = otp_service.verify_otp(email, otp)

        assert is_valid is True
        assert error is None
        assert email not in otp_service.otp_store  # Should be cleaned up

    def test_verify_otp_invalid(self):
        """Verificar que un OTP inválido devuelve error."""
        otp_service = OTPService()
        email = "admin@example.com"

        otp_service.generate_otp(email)
        is_valid, error = otp_service.verify_otp(email, "000000")

        assert is_valid is False
        assert error is not None
        assert "Invalid OTP" in error
        assert "2 attempts remaining" in error

    def test_verify_otp_expired(self):
        """Verificar que un OTP expirado devuelve error."""
        otp_service = OTPService()
        email = "admin@example.com"

        otp = otp_service.generate_otp(email)

        # Forzar expiración manualmente
        otp_service.otp_store[email]["expiry"] = datetime.now() - timedelta(minutes=1)

        is_valid, error = otp_service.verify_otp(email, otp)

        assert is_valid is False
        assert error is not None
        assert "OTP expired" in error

    def test_verify_otp_max_attempts(self):
        """Verificar que después de 3 intentos fallidos se bloquea."""
        otp_service = OTPService()
        email = "admin@example.com"

        otp = otp_service.generate_otp(email)

        # 3 intentos fallidos
        for _ in range(3):
            is_valid, _ = otp_service.verify_otp(email, "000000")

        # El 4to intento debería fallar porque el OTP fue eliminado
        is_valid, error = otp_service.verify_otp(email, otp)

        assert is_valid is False
        assert error is not None
        assert "No OTP found" in error or "Maximum attempts" in error

    def test_verify_otp_already_verified(self):
        """Verificar que un OTP ya verificado no se puede reusar."""
        otp_service = OTPService()
        email = "admin@example.com"

        otp = otp_service.generate_otp(email)
        otp_service.verify_otp(email, otp)  # Verificar primero

        # Intentar verificar de nuevo
        is_valid, error = otp_service.verify_otp(email, otp)

        assert is_valid is False
        assert error is not None
        assert "already verified" in error.lower()

    def test_verify_otp_missing_email(self):
        """Verificar que lanza error para email inexistente."""
        otp_service = OTPService()

        is_valid, error = otp_service.verify_otp("nonexistent@example.com", "123456")

        assert is_valid is False
        assert error is not None
        assert "No OTP found" in error

    def test_verify_otp_empty_inputs(self):
        """Verificar que lanza error para inputs vacíos."""
        otp_service = OTPService()

        is_valid, error = otp_service.verify_otp("", "")

        assert is_valid is False
        assert error is not None
        assert "required" in error.lower()


class TestOTPServiceCleanup:
    """Tests para la limpieza de OTPs expirados."""

    def test_cleanup_expired_otps(self):
        ."""Verificar que se limpian los OTPs expirados."""
        otp_service = OTPService()

        # Crear 3 OTPs
        otp_service.generate_otp("admin1@example.com")
        otp_service.generate_otp("admin2@example.com")
        otp_service.generate_otp("admin3@example.com")

        # Expirar uno manualmente
        otp_service.otp_store["admin2@example.com"]["expiry"] = (
            datetime.now() - timedelta(minutes=1)
        )

        # Limpiar expirados
        removed = otp_service.cleanup_expired()

        assert removed == 1
        assert "admin2@example.com" not in otp_service.otp_store
        assert "admin1@example.com" in otp_service.otp_store
        assert "admin3@example.com" in otp_service.otp_store


class TestOTPServiceStatus:
    """Tests para obtener estado de OTPs."""

    def test_get_otp_status_existing(self):
        ."""Verificar que se obtiene el estado de un OTP existente."""
        otp_service = OTPService()
        email = "admin@example.com"

        otp_service.generate_otp(email)
        status = otp_service.get_otp_status(email)

        assert status is not None
        assert status["email"] == email
        assert "created_at" in status
        assert "expiry" in status
        assert "attempts" in status
        assert "verified" in status
        assert "expired" in status
        assert status["verified"] is False

    def test_get_otp_status_nonexistent(self):
        """Verificar que devuelve None para OTP inexistente."""
        otp_service = OTPService()

        status = otp_service.get_otp_status("nonexistent@example.com")

        assert status is None

    def test_get_otp_status_expired(self):
        """Verificar que el estado marca correctamente expirado."""
        otp_service = OTPService()
        email = "admin@example.com"

        otp_service.generate_otp(email)
        # Forzar expiración
        otp_service.otp_store[email]["expiry"] = datetime.now() - timedelta(minutes=1)

        status = otp_service.get_otp_status(email)

        assert status["expired"] is True


class TestOTPServiceConstants:
    """Tests para las constantes del servicio OTP."""

    def test_otp_expiry_minutes(self):
        ."""Verificar que el expiry es de 10 minutos."""
        otp_service = OTPService()

        assert otp_service.otp_expiry_minutes == 10

    def test_max_attempts(self):
        ."""Verificar que el máximo de intentos es 3."""
        otp_service = OTPService()

        assert otp_service.max_attempts == 3

    def test_otp_length(self):
        ."""Verificar que el OTP tiene 6 dígitos."""
        otp_service = OTPService()

        assert otp_service.otp_length == 6


class TestOTPServiceSingleton:
    ."""Tests para la instancia singleton."""

    def test_singleton_instance_exists(self):
        ."""Verificar que existe una instancia singleton."""
        from app.security.otp_service import otp_service

        assert otp_service is not None
        assert isinstance(otp_service, OTPService)

    def test_singleton_is_same_instance(self):
        ."""Verificar que múltiples imports devuelven la misma instancia."""
        from app.security.otp_service import otp_service as otp1
        from app.security.otp_service import otp_service as otp2

        assert otp1 is otp2
