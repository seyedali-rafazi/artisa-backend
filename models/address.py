"""Address Document Model."""

from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field


class Address(Document):
    """User Saved Address model."""

    userId: Indexed(str)  # type: ignore
    title: str
    fullName: str
    phone: str
    province: str
    city: str
    postalCode: str
    addressLine: str
    isDefault: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "addresses"
