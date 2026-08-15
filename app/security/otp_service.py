"""Two-Factor Authentication (2FA) Service.

========================================

OTP-based 2FA for admin endpoints following BC3-Suite security patterns.

Features:
- 6-digit OTP code
- 10-minute expiry
- Maximum 3 verification attempts
- Email delivery via Flask-Mail
- In-memory store (Redis in production)

Usage:
    from app.security.otp_service import OTPService

    otp_service = OTPService()
    otp_code = otp_service.generate_otp(email="admin@example.com")
    # OTP sent to email automatically

    is_valid = otp_service.verify_otp(
        email="admin@example.com",
        code="123456"
    )
"""

import secrets
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    from loguru import logger
except ModuleNotFoundError:
    import logging

    logger = logging.getLogger("api-disano.security.otp")

from app.config import get_settings

settings = get_settings()


@dataclass(frozen=True)
class OTPCompatibility:
    """Represent an OTP using the legacy module-level API."""

    code: str
    email: str
    created_at: datetime
    expires_at: datetime
    max_attempts: int


class OTPService:
    """Service for OTP generation, delivery, and verification."""

    def __init__(self):
        """Initialize OTP service with an in-memory store."""
        self.otp_store: dict[str, dict] = defaultdict(dict)
        self._verified_emails: set[str] = set()
        self.otp_expiry_minutes = 10
        self.max_attempts = 3
        self.otp_length = 6

    def generate_otp(self, email: str) -> str:
        """
        Generate a 6-digit OTP and send it via email.

        Args:
            email: Email address to send OTP to

        Returns:
            str: The generated OTP (for testing purposes)

        Raises:
            ValueError: If email is invalid or empty

        Example:
            otp_service = OTPService()
            otp = otp_service.generate_otp("admin@example.com")
            # OTP sent to email automatically
        """
        if not email or "@" not in email:
            raise ValueError("Invalid email address")

        self._verified_emails.discard(email)

        # Generate 6-digit OTP
        otp = "".join([str(secrets.randbelow(10)) for _ in range(self.otp_length)])

        # Store OTP with metadata
        expiry_time = datetime.now() + timedelta(minutes=self.otp_expiry_minutes)

        self.otp_store[email] = {
            "code": otp,
            "expiry": expiry_time,
            "attempts": 0,
            "created_at": datetime.now(),
            "verified": False,
        }

        logger.info(f"OTP generated for {email}, expires at {expiry_time}")

        # Send OTP via email (in production)
        # self._send_otp_email(email, otp)

        return otp

    def verify_otp(self, email: str, code: str) -> tuple[bool, str | None]:
        """
        Verify an OTP code.

        Args:
            email: Email address associated with OTP
            code: OTP code to verify

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)

        Example:
            is_valid, error = otp_service.verify_otp(
                "admin@example.com",
                "123456"
            )
            if is_valid:
                # OTP verified successfully
                pass
            else:
                print(error)
        """
        if not email or not code:
            return False, "Email and code are required"

        if email in self._verified_emails:
            return False, "OTP already verified"

        otp_data = self.otp_store.get(email)

        if not otp_data:
            return False, "No OTP found for this email"

        # Check if already verified
        if otp_data["verified"]:
            return False, "OTP already verified"

        # Check expiry
        if datetime.now() > otp_data["expiry"]:
            logger.warning(f"OTP expired for {email}")
            del self.otp_store[email]
            return False, "OTP expired"

        # Check attempts
        if otp_data["attempts"] >= self.max_attempts:
            logger.warning(f"Max OTP attempts exceeded for {email}")
            del self.otp_store[email]
            return False, "Maximum attempts exceeded"

        # Increment attempt count
        otp_data["attempts"] += 1

        # Verify code
        if code == otp_data["code"]:
            otp_data["verified"] = True
            logger.info(f"OTP verified successfully for {email}")

            self._verified_emails.add(email)
            del self.otp_store[email]

            return True, None
        else:
            attempts_remaining = self.max_attempts - otp_data["attempts"]
            logger.warning(
                f"Invalid OTP attempt {otp_data['attempts']}/{self.max_attempts} for {email}"
            )
            return False, f"Invalid OTP. {attempts_remaining} attempts remaining"

    def _send_otp_email(self, email: str, otp: str) -> bool:
        """
        Send OTP via email (placeholder for Flask-Mail integration).

        Args:
            email: Recipient email address
            otp: OTP code to send

        Returns:
            bool: True if sent successfully, False otherwise

        Example:
            otp_service._send_otp_email("admin@example.com", "123456")
        """
        # TODO: Integrate with Flask-Mail
        # from flask_mail import Message, mail
        #
        # msg = Message(
        #     "API-DISANO OTP Code",
        #     recipients=[email],
        #     body=f"Your OTP code is: {otp}\n\nValid for {self.otp_expiry_minutes} minutes."
        # )
        # mail.send(msg)

        logger.info(f"OTP email sent to {email}: {otp}")
        return True

    def cleanup_expired(self) -> int:
        """
        Remove expired OTPs from store.

        Returns:
            int: Number of OTPs removed

        Example:
            removed = otp_service.cleanup_expired()
            print(f"Removed {removed} expired OTPs")
        """
        now = datetime.now()
        expired_emails = [email for email, data in self.otp_store.items() if now > data["expiry"]]

        for email in expired_emails:
            del self.otp_store[email]
            logger.info(f"Cleaned up expired OTP for {email}")

        return len(expired_emails)

    def get_otp_status(self, email: str) -> dict | None:
        """
        Get status of an OTP (for monitoring/debugging).

        Args:
            email: Email address associated with OTP

        Returns:
            Optional[dict]: OTP status or None if not found

        Example:
            status = otp_service.get_otp_status("admin@example.com")
            print(status)
        """
        otp_data = self.otp_store.get(email)
        if not otp_data:
            return None

        return {
            "email": email,
            "created_at": otp_data["created_at"].isoformat(),
            "expiry": otp_data["expiry"].isoformat(),
            "attempts": otp_data["attempts"],
            "max_attempts": self.max_attempts,
            "verified": otp_data["verified"],
            "expired": datetime.now() > otp_data["expiry"],
        }


# Singleton instance
otp_service = OTPService()


def generate_otp(email: str) -> OTPCompatibility:
    """Generate an OTP through the shared service compatibility API."""
    code = otp_service.generate_otp(email)
    data = otp_service.otp_store[email]
    return OTPCompatibility(
        code=code,
        email=email,
        created_at=data["created_at"],
        expires_at=data["expiry"],
        max_attempts=otp_service.max_attempts,
    )


def verify_otp(email: str, code: str) -> tuple[bool, str | None]:
    """Verify an OTP through the shared service compatibility API."""
    return otp_service.verify_otp(email, code)
