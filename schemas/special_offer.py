"""Special Offer Pydantic Schemas for validation and serialization."""

from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

from core.timezone import to_utc, format_tehran_iso, get_offer_status


class SpecialOfferProductSummary(BaseModel):
    """Lightweight product representation inside a special offer."""

    id: str
    name: str
    nameEn: Optional[str] = ""
    price: float
    oldPrice: Optional[float] = None
    image: str
    category: str
    categoryEn: Optional[str] = ""
    rating: float = 5.0
    stock_quantity: int = 100
    status: str = "published"


class SpecialOfferCreate(BaseModel):
    """Schema for creating a special offer."""

    title: str = Field(..., min_length=2, max_length=200, description="Title of the special offer")
    description: Optional[str] = Field(None, max_length=2000, description="Optional offer description")
    product_ids: List[str] = Field(..., min_items=1, description="List of product IDs included in the offer")
    start_at: datetime = Field(..., description="Start date and time (timezone-aware or Tehran local)")
    end_at: datetime = Field(..., description="End date and time (timezone-aware or Tehran local)")
    is_active: bool = Field(True, description="Manual toggle to activate/deactivate offer")

    @field_validator("product_ids")
    @classmethod
    def clean_product_ids(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("حداقل یک محصول باید انتخاب شود")
        
        # Deduplicate while preserving order and strip whitespace
        cleaned = []
        seen = set()
        for pid in v:
            if not isinstance(pid, str):
                pid = str(pid)
            pid = pid.strip()
            if pid and pid not in seen:
                seen.add(pid)
                cleaned.append(pid)
                
        if not cleaned:
            raise ValueError("شناسه‌های محصول نامعتبر هستند")
        return cleaned

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("عنوان پیشنهاد باید حداقل ۲ کاراکتر باشد")
        return v

    @model_validator(mode="after")
    def validate_date_range_and_normalize(self) -> "SpecialOfferCreate":
        # Normalize to UTC
        self.start_at = to_utc(self.start_at)
        self.end_at = to_utc(self.end_at)

        if self.end_at <= self.start_at:
            raise ValueError("زمان پایان پیشنهاد باید بعد از زمان شروع باشد")

        return self


class SpecialOfferUpdate(BaseModel):
    """Schema for updating a special offer."""

    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    product_ids: Optional[List[str]] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_active: Optional[bool] = None

    @field_validator("product_ids")
    @classmethod
    def clean_product_ids(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        cleaned = []
        seen = set()
        for pid in v:
            if not isinstance(pid, str):
                pid = str(pid)
            pid = pid.strip()
            if pid and pid not in seen:
                seen.add(pid)
                cleaned.append(pid)
        if not cleaned:
            raise ValueError("حداقل یک محصول باید برای پیشنهاد انتخاب شود")
        return cleaned

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("عنوان پیشنهاد باید حداقل ۲ کاراکتر باشد")
        return v


class SpecialOfferResponse(BaseModel):
    """Schema for Special Offer serialized response."""

    id: str
    title: str
    description: Optional[str] = None
    product_ids: List[str]
    products: List[SpecialOfferProductSummary] = Field(default_factory=list)
    start_at: datetime
    end_at: datetime
    start_at_tehran: str
    end_at_tehran: str
    is_active: bool
    status: str  # "active", "upcoming", "expired", "inactive"
    created_at: datetime
    updated_at: datetime


class PaginatedSpecialOffersResponse(BaseModel):
    """Paginated list of special offers."""

    items: List[SpecialOfferResponse]
    total: int
    page: int
    limit: int
    total_pages: int
