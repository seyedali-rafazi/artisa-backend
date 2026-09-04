"""FAQ Schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class FAQResponse(BaseModel):
    """FAQ response schema with dual question/q and answer/a fields for backward compatibility."""

    id: str
    question: str
    answer: str
    q: Optional[str] = None
    a: Optional[str] = None
    order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FAQCreateRequest(BaseModel):
    """Payload for creating a new FAQ item."""

    question: str = Field(..., min_length=2, max_length=500, description="عنوان یا متن سوال")
    answer: str = Field(..., min_length=2, description="پاسخ تفصیلی سوال")
    order: Optional[int] = Field(0, description="ترتیب نمایش")
    is_active: Optional[bool] = Field(True, description="وضعیت انتشار")


class FAQUpdateRequest(BaseModel):
    """Payload for updating an existing FAQ item."""

    question: Optional[str] = Field(None, min_length=2, max_length=500, description="عنوان یا متن سوال")
    answer: Optional[str] = Field(None, min_length=2, description="پاسخ تفصیلی سوال")
    order: Optional[int] = Field(None, description="ترتیب نمایش")
    is_active: Optional[bool] = Field(None, description="وضعیت انتشار")


class FAQReorderItem(BaseModel):
    """Single item in a batch reorder payload."""

    id: str
    order: int


class FAQReorderRequest(BaseModel):
    """Payload for reordering multiple FAQ items at once."""

    items: List[FAQReorderItem]
