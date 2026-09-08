"""Specification Setting Pydantic Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SpecificationSettingResponse(BaseModel):
    """Specification setting response schema."""

    id: str
    title: str
    default_value: Optional[str] = ""
    category: Optional[str] = None
    description: Optional[str] = None
    order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SpecificationSettingCreate(BaseModel):
    """Payload for creating a new specification setting preset."""

    title: str = Field(..., min_length=1, max_length=100, description="نام ویژگی یا مشخصه فنی")
    default_value: Optional[str] = Field("", max_length=255, description="مقدار پیش‌فرض پیشنهادی")
    category: Optional[str] = Field(None, max_length=100, description="دسته‌بندی محصول مرتبط")
    description: Optional[str] = Field(None, max_length=500, description="توضیحات راهنما برای مدیر")
    order: Optional[int] = Field(0, description="ترتیب نمایش")
    is_active: Optional[bool] = Field(True, description="وضعیت فعال بودن")


class SpecificationSettingUpdate(BaseModel):
    """Payload for updating an existing specification setting preset."""

    title: Optional[str] = Field(None, min_length=1, max_length=100, description="نام ویژگی یا مشخصه فنی")
    default_value: Optional[str] = Field(None, max_length=255, description="مقدار پیش‌فرض پیشنهادی")
    category: Optional[str] = Field(None, max_length=100, description="دسته‌بندی محصول مرتبط")
    description: Optional[str] = Field(None, max_length=500, description="توضیحات راهنما برای مدیر")
    order: Optional[int] = Field(None, description="ترتیب نمایش")
    is_active: Optional[bool] = Field(None, description="وضعیت فعال بودن")
