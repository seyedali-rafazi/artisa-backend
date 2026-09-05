"""Newsletter Schemas for validation and serialization."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class NewsletterSubscribeRequest(BaseModel):
    """Schema for subscribing to newsletter."""

    email: EmailStr = Field(
        ...,
        description="Valid email address to subscribe to newsletter",
        examples=["user@example.com"],
    )

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip().lower()
        if not v:
            raise ValueError("آدرس ایمیل الزامی است")
        return v


class NewsletterSubscriberResponse(BaseModel):
    """Schema for serialized subscriber item."""

    id: str
    email: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginatedNewsletterSubscribersResponse(BaseModel):
    """Paginated response for admin newsletter subscribers."""

    items: List[NewsletterSubscriberResponse]
    total: int
    page: int
    limit: int
    total_pages: int
    active_count: int = 0
