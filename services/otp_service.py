"""OTP Service for 4-digit code generation, hashing, rate limiting, and verification."""

import hashlib
import random
from datetime import datetime, timedelta
from typing import Tuple, Optional
from models.verification_code import VerificationCode


class OTPService:
    """Service handling 4-digit OTP lifecycle."""

    CODE_LIFETIME_MINUTES = 10
    RESEND_COOLDOWN_SECONDS = 60
    MAX_ATTEMPTS = 5

    @staticmethod
    def _hash_code(code: str) -> str:
        """Hash the 4-digit code using SHA-256."""
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @classmethod
    def generate_code(cls) -> str:
        """Generate a secure 4-digit numeric string (e.g. '4281')."""
        return f"{random.randint(1000, 9999)}"

    @classmethod
    async def create_verification_code(
        cls, user_id: str, email: str, code_type: str
    ) -> Tuple[Optional[str], Optional[int]]:
        """Create a new 4-digit verification code.

        Returns (raw_code, None) on success, or (None, seconds_remaining) if rate-limited.
        """
        now = datetime.utcnow()

        # Check existing active code for rate limit
        existing = await VerificationCode.find_one(
            VerificationCode.email == email,
            VerificationCode.code_type == code_type,
            VerificationCode.is_used == False,
            VerificationCode.expires_at > now,
        )

        if existing:
            elapsed = (now - existing.last_sent_at).total_seconds()
            if elapsed < cls.RESEND_COOLDOWN_SECONDS:
                remaining = int(cls.RESEND_COOLDOWN_SECONDS - elapsed)
                return None, remaining

            # Invalidate existing code before creating new one
            existing.is_used = True
            await existing.save()

        # Invalidate any other old codes for this email and type
        old_codes = await VerificationCode.find(
            VerificationCode.email == email,
            VerificationCode.code_type == code_type,
            VerificationCode.is_used == False,
        ).to_list()
        for old in old_codes:
            old.is_used = True
            await old.save()

        # Generate new 4-digit code
        raw_code = cls.generate_code()
        hashed_code = cls._hash_code(raw_code)
        expires_at = now + timedelta(minutes=cls.CODE_LIFETIME_MINUTES)

        code_doc = VerificationCode(
            user_id=user_id,
            email=email,
            hashed_code=hashed_code,
            code_type=code_type,
            is_used=False,
            attempts=0,
            expires_at=expires_at,
            last_sent_at=now,
            created_at=now,
        )
        await code_doc.insert()

        return raw_code, None

    @classmethod
    async def verify_code(
        cls, email: str, code: str, code_type: str
    ) -> Tuple[bool, str]:
        """Verify the user-entered 4-digit code.

        Returns (is_valid, error_message).
        """
        now = datetime.utcnow()

        # Find latest active code
        code_doc = (
            await VerificationCode.find(
                VerificationCode.email == email,
                VerificationCode.code_type == code_type,
                VerificationCode.is_used == False,
            )
            .sort("-created_at")
            .first_or_none()
        )

        if not code_doc:
            return False, "کد تایید یافت نشد یا قبلاً استفاده شده است"

        if code_doc.expires_at < now:
            code_doc.is_used = True
            await code_doc.save()
            return False, "کد تایید منقضی شده است. لطفاً درخواست کد جدید کنید"

        if code_doc.attempts >= cls.MAX_ATTEMPTS:
            code_doc.is_used = True
            await code_doc.save()
            return False, "تعداد تلاش‌های ناموفق بیش از حد مجاز است. کد جدید دریافت کنید"

        # Increment attempt counter
        code_doc.attempts += 1
        await code_doc.save()

        hashed_input = cls._hash_code(code.strip())
        if hashed_input != code_doc.hashed_code:
            return False, "کد تایید وارد شده اشتباه است"

        # Mark code as used upon successful match
        code_doc.is_used = True
        await code_doc.save()

        return True, "کد تایید با موفقیت تایید شد"
