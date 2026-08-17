"""Special Offer Document Model for scheduled discount campaigns."""

from datetime import datetime
from typing import List, Optional
import pymongo
from beanie import Document, Indexed
from pydantic import Field

from core.timezone import now_utc, get_offer_status, to_tehran, format_tehran_iso


class SpecialOffer(Document):
    """Special Offer / Discount Campaign MongoDB model."""

    title: Indexed(str)  # type: ignore
    description: Optional[str] = None
    product_ids: List[str] = Field(default_factory=list)
    start_at: datetime  # UTC-aware datetime
    end_at: datetime    # UTC-aware datetime
    is_active: bool = True
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    class Settings:
        name = "special_offers"
        indexes = [
            # Compound index for fast active offer lifecycle queries
            [
                ("is_active", pymongo.ASCENDING),
                ("start_at", pymongo.ASCENDING),
                ("end_at", pymongo.ASCENDING),
            ],
            [
                ("start_at", pymongo.ASCENDING),
                ("end_at", pymongo.ASCENDING),
            ],
            [
                ("created_at", pymongo.DESCENDING),
            ],
            "product_ids",
        ]

    @property
    def current_status(self) -> str:
        """Dynamic lifecycle status computed at runtime: active, upcoming, expired, or inactive."""
        return get_offer_status(self.start_at, self.end_at, self.is_active)

    @property
    def start_at_tehran(self) -> str:
        """ISO formatted string in Asia/Tehran timezone."""
        return format_tehran_iso(self.start_at)

    @property
    def end_at_tehran(self) -> str:
        """ISO formatted string in Asia/Tehran timezone."""
        return format_tehran_iso(self.end_at)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "جشنواره تابستانه تخفیف‌های طلایی",
                "description": "تخفیف ویژه تا ۳۰٪ روی برترین تابلوهای نقاشی دست‌ساز",
                "product_ids": ["6581f...", "6582a..."],
                "start_at": "2026-08-17T00:00:00Z",
                "end_at": "2026-08-25T23:59:59Z",
                "is_active": True,
            }
        }
