"""FAQ Document Model."""

from datetime import datetime
from beanie import Document
from pydantic import Field


class FAQ(Document):
    """FAQ model."""

    question: str
    answer: str
    order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "faqs"
        indexes = [
            "order",
            "is_active",
            [("created_at", -1)],
        ]
