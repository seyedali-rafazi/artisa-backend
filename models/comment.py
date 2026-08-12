"""Comment Document Model."""

from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field


class Comment(Document):
    """Product Review / Comment model."""

    productId: Indexed(str)  # type: ignore
    userId: Optional[str] = None
    userName: str = "کاربر غیررسمی"
    userEmail: Optional[str] = None
    text: str
    rating: int = Field(default=5, ge=1, le=5)
    type: str = "comment"  # comment or question
    reply: Optional[str] = None
    replyDate: Optional[str] = None
    status: str = "approved"  # approved, pending, rejected
    is_deleted: bool = False
    moderated_by: Optional[str] = None
    moderated_at: Optional[datetime] = None
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y/%m/%d"))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "comments"
        indexes = [
            [("productId", 1), ("is_deleted", 1), ("created_at", -1)],
            [("userId", 1), ("created_at", -1)],
            [("status", 1)],
        ]

