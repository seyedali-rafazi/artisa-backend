"""Comment Pydantic Schemas."""

import html
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class CommentCreate(BaseModel):
    """Payload for creating a product comment/review or question."""

    text: str = Field(..., min_length=3, max_length=1000, description="Comment text")
    rating: int = Field(default=5, ge=1, le=5, description="Rating from 1 to 5")
    name: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = Field("comment", description="comment or question")

    @field_validator("text", mode="before")
    @classmethod
    def sanitize_and_trim_text(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("متن نظر باید رشته متنی باشد")
        stripped = v.strip()
        if not stripped:
            raise ValueError("متن نظر نمی‌تواند خالی باشد")
        # Sanitize HTML tags to prevent XSS attacks
        return html.escape(stripped)


class CommentUpdate(BaseModel):
    """Payload for updating a user's comment."""

    text: Optional[str] = Field(None, min_length=3, max_length=1000)
    rating: Optional[int] = Field(None, ge=1, le=5)

    @field_validator("text", mode="before")
    @classmethod
    def sanitize_and_trim_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("متن نظر باید رشته متنی باشد")
        stripped = v.strip()
        if not stripped:
            raise ValueError("متن نظر نمی‌تواند خالی باشد")
        return html.escape(stripped)


class CommentAdminUpdate(BaseModel):
    """Payload for admin comment moderation."""

    status: Optional[str] = Field(None, description="approved, pending, or rejected")
    text: Optional[str] = Field(None, min_length=3, max_length=1000)
    rating: Optional[int] = Field(None, ge=1, le=5)
    type: Optional[str] = Field(None, description="comment or question")
    reply: Optional[str] = Field(None, description="Admin reply to comment/question")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["approved", "pending", "rejected"]:
            raise ValueError("وضعیت نظر باید یکی از موارد approved، pending یا rejected باشد")
        return v


class CommentResponse(BaseModel):
    """Response schema for a single comment."""

    id: str
    productId: str
    userId: Optional[str] = None
    userName: str
    userEmail: Optional[str] = None
    text: str
    rating: int
    type: Optional[str] = "comment"
    reply: Optional[str] = None
    replyDate: Optional[str] = None
    status: str = "approved"
    date: str
    created_at: Optional[datetime] = None
    productName: Optional[str] = None


class PaginatedCommentsResponse(BaseModel):
    """Paginated list of comments."""

    items: List[CommentResponse]
    total: int
    page: int
    limit: int
    total_pages: int

