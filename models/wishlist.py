"""Wishlist Document Model."""

from datetime import datetime
from typing import List
from beanie import Document, Indexed
from pydantic import Field


class Wishlist(Document):
    """User Wishlist document model."""

    userId: Indexed(str, unique=True)  # type: ignore
    productIds: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "wishlists"
