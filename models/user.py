"""User Document Model."""

from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field, EmailStr


class User(Document):
    """User MongoDB model."""

    name: str
    email: Indexed(str, unique=True)  # type: ignore
    hashed_password: str
    phone: Optional[str] = None
    role: str = "کاربر عادی"  # "کاربر عادی", "مدیر سیستم"
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "علی رضایی",
                "email": "user@example.com",
                "phone": "09121234567",
                "role": "کاربر عادی",
            }
        }
