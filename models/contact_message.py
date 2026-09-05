"""Contact Message Document Model."""

from datetime import datetime
from beanie import Document
from pydantic import Field


class ContactMessage(Document):
    """Contact Message document model for messages submitted via Contact Us form."""

    name: str
    email: str
    message: str
    status: str = "unread"  # "unread" | "read"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "contact_messages"
        indexes = [
            "status",
            "email",
            [("created_at", -1)],
        ]
