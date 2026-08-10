"""Favorite Document Model."""

from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field
import pymongo


class Favorite(Document):
    """User Favorite product document model."""

    user_id: Indexed(str)  # type: ignore
    product_id: Indexed(str)  # type: ignore
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "favorites"
        indexes = [
            pymongo.IndexModel(
                [("user_id", pymongo.ASCENDING), ("product_id", pymongo.ASCENDING)],
                unique=True,
                name="unique_user_product_favorite",
            )
        ]
