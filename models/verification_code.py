"""Verification Code Document Model."""

from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field


class VerificationCode(Document):
    """MongoDB model for 4-digit verification codes (Email verification & Password reset)."""

    user_id: Indexed(str)  # type: ignore
    email: Indexed(str)  # type: ignore
    hashed_code: str
    code_type: str  # "email_verification" or "password_reset"
    is_used: bool = False
    attempts: int = 0  # Max 5 attempts
    expires_at: datetime
    last_sent_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "verification_codes"
