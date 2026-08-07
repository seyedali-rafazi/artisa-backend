"""User Document Model."""

from datetime import datetime
from typing import Optional
from enum import Enum
from beanie import Document, Indexed
from pydantic import Field, EmailStr


class RoleEnum(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Document):
    """User MongoDB model."""

    name: str
    email: Indexed(str, unique=True)  # type: ignore
    hashed_password: Optional[str] = None
    phone: Optional[str] = None
    google_id: Optional[str] = None
    provider: str = "local"  # "local", "google"
    avatar: Optional[str] = None
    email_verified: bool = False
    is_verified: bool = False
    role: str = "customer"  # "customer", "admin", "super_admin", or legacy "کاربر عادی", "مدیر سیستم"
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def normalized_role(self) -> str:
        """Return standardized role string."""
        if self.is_superuser or self.role in ["super_admin", "مدیر ارشد"]:
            return RoleEnum.SUPER_ADMIN.value
        if self.role in ["admin", "مدیر سیستم", "مدیر"]:
            return RoleEnum.ADMIN.value
        return RoleEnum.CUSTOMER.value

    @property
    def is_admin_user(self) -> bool:
        """Check if user has admin or super admin privileges."""
        return self.normalized_role in [RoleEnum.ADMIN.value, RoleEnum.SUPER_ADMIN.value]

    @property
    def is_super_admin_user(self) -> bool:
        """Check if user is super admin."""
        return self.normalized_role == RoleEnum.SUPER_ADMIN.value

    class Settings:
        name = "users"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "علی رضایی",
                "email": "user@example.com",
                "phone": "09121234567",
                "role": "customer",
            }
        }
