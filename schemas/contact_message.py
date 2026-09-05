"""Contact Message Schemas for validation and serialization."""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class ContactMessageCreate(BaseModel):
    """Schema for incoming public contact message submissions."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of sender",
        examples=["علی محمدی"],
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address of sender",
        examples=["user@example.com"],
    )
    message: str = Field(
        ...,
        min_length=5,
        max_length=4000,
        description="Message content or inquiry",
        examples=["سلام، سوالی در مورد نحوه سفارش تابلوی نقاشی داشتم."],
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v or len(v) < 2:
            raise ValueError("نام باید حداقل ۲ کاراکتر باشد")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip().lower()
        if not v:
            raise ValueError("آدرس ایمیل الزامی است")
        return v

    @field_validator("message", mode="before")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        if not v or len(v) < 5:
            raise ValueError("متن پیام باید حداقل ۵ کاراکتر باشد")
        return v


class ContactMessageStatusUpdate(BaseModel):
    """Schema for updating contact message status (read / unread)."""

    status: Literal["unread", "read"] = Field(
        ...,
        description="Read status of message: unread or read",
    )


class ContactMessageResponse(BaseModel):
    """Schema for serialized contact message item."""

    id: str
    name: str
    email: str
    message: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginatedContactMessagesResponse(BaseModel):
    """Paginated list of contact messages for admin view."""

    items: List[ContactMessageResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    unread_count: int = 0
