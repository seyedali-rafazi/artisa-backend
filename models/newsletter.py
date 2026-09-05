"""Newsletter Subscriber Document Model."""

from datetime import datetime
from beanie import Document
from pydantic import Field


class NewsletterSubscriber(Document):
    """Newsletter subscriber document model."""

    email: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "newsletter_subscribers"
        indexes = [
            "email",
            "is_active",
            [("created_at", -1)],
        ]
