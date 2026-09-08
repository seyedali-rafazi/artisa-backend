"""Product Specification Setting Document Model."""

from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field


class SpecificationSetting(Document):
    """Product Specification Setting / Preset model."""

    title: str
    default_value: Optional[str] = ""
    category: Optional[str] = None
    description: Optional[str] = None
    order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "specification_settings"
        indexes = [
            "title",
            "category",
            "order",
            "is_active",
            [("created_at", -1)],
        ]
