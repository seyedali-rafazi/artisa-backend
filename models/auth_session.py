"""Auth Session Document Model for tracking refresh tokens and active user sessions."""

from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field


class AuthSession(Document):
    """MongoDB model for Refresh Tokens and User Sessions.

    Security design:
    - `refresh_token_hash`: Only the SHA-256 hash of the refresh token is stored.
      Raw tokens are never stored in the database.
    - `token_family_id`: Groups rotated refresh tokens belonging to the same
      login session to detect and mitigate token theft.
    - `revoked_at`: Timestamp when the session was explicitly revoked or rotated.
    - `replaced_by`: ID of the successor session record when rotated.
    """

    user_id: Indexed(str)  # type: ignore
    token_family_id: Indexed(str)  # type: ignore
    refresh_token_hash: Indexed(str, unique=True)  # type: ignore
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Indexed(datetime)  # type: ignore
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    replaced_by: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    device_info: Optional[str] = None
    is_active: bool = True

    @property
    def is_expired(self) -> bool:
        """Check whether the session has reached its expiration time."""
        return datetime.utcnow() >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check whether the session is currently valid for rotation."""
        return self.is_active and self.revoked_at is None and not self.is_expired

    class Settings:
        name = "auth_sessions"
        indexes = [
            "user_id",
            "token_family_id",
            "refresh_token_hash",
            "expires_at",
            "is_active",
        ]
