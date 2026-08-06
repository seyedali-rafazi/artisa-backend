"""Comment Document Model."""

from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field


class Comment(Document):
    """Product Review / Comment model."""

    productId: Indexed(str)  # type: ignore
    userId: Optional[str] = None
    userName: str = "کاربر مهمان"
    text: str
    rating: int = Field(default=5, ge=1, le=5)
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y/%m/%d"))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "comments"
