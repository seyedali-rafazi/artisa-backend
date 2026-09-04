"""Banner Schemas for Hero Slider & Admin Banner Management."""

from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class BannerPositionSchema(BaseModel):
    """Normalized percentage coordinates (0 - 100)."""

    x: float = Field(default=50.0, ge=0.0, le=100.0, description="Horizontal X position percentage (0-100)")
    y: float = Field(default=50.0, ge=0.0, le=100.0, description="Vertical Y position percentage (0-100)")


class BannerTextElementSchema(BaseModel):
    """Typography overlay element."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(..., min_length=1, max_length=500, description="Text string")
    fontFamily: str = Field(default="inherit", description="Font family")
    fontSize: int = Field(default=24, ge=8, le=140, description="Font size in px")
    fontWeight: str = Field(default="normal", description="Font weight (e.g. 400, 500, 600, 700, 800)")
    color: str = Field(default="#FFFFFF", description="Text color code")
    textAlign: str = Field(default="center", description="Text alignment: right, center, left")
    lineHeight: Optional[float] = Field(default=1.4, description="Line height multiplier")
    letterSpacing: Optional[float] = Field(default=0.0, description="Letter spacing in px")
    textShadow: Optional[str] = Field(default=None, description="CSS text shadow string")
    position: BannerPositionSchema = Field(default_factory=BannerPositionSchema)
    scaleX: Optional[float] = Field(default=1.0, ge=0.1, le=10.0, description="Horizontal scale multiplier")
    scaleY: Optional[float] = Field(default=1.0, ge=0.1, le=10.0, description="Vertical scale multiplier")


class BannerCreateRequest(BaseModel):
    """Payload to create a new banner."""

    title: str = Field(..., min_length=1, max_length=200, description="Banner title")
    image: str = Field(..., min_length=1, description="Vercel Blob image URL")
    texts: List[BannerTextElementSchema] = Field(default_factory=list, description="List of text overlays")
    link: Optional[str] = Field(default="", description="Target route or URL")
    linkOpenInNewTab: Optional[bool] = Field(default=False, description="Open link in new tab")
    isActive: Optional[bool] = Field(default=True, description="Active status")
    order: Optional[int] = Field(default=0, description="Display order sequence")

    # Optional legacy fields
    subtitle: Optional[str] = Field(default="", description="Legacy subtitle")
    badge: Optional[str] = Field(default="", description="Legacy badge")
    buttonText: Optional[str] = Field(default="", description="Legacy CTA button text")


class BannerUpdateRequest(BaseModel):
    """Payload to update an existing banner."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    image: Optional[str] = Field(None, min_length=1)
    texts: Optional[List[BannerTextElementSchema]] = None
    link: Optional[str] = None
    linkOpenInNewTab: Optional[bool] = None
    isActive: Optional[bool] = None
    order: Optional[int] = None

    # Optional legacy fields
    subtitle: Optional[str] = None
    badge: Optional[str] = None
    buttonText: Optional[str] = None


class BannerStatusUpdateRequest(BaseModel):
    """Payload to quick toggle active status."""

    isActive: bool = Field(..., description="Active status flag")


class BannerReorderItem(BaseModel):
    """Single item in reorder list."""

    id: str = Field(..., description="Banner ID")
    order: int = Field(..., description="New display order")


class BannerReorderRequest(BaseModel):
    """Payload to batch update banner sequence order."""

    items: List[BannerReorderItem] = Field(..., min_length=1, description="List of banner order updates")


class BannerResponse(BaseModel):
    """Full response schema for public and admin banner views."""

    id: str
    title: str
    image: str
    texts: List[BannerTextElementSchema] = Field(default_factory=list)
    link: Optional[str] = ""
    linkOpenInNewTab: bool = False
    isActive: bool = True
    order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Legacy fields
    subtitle: Optional[str] = ""
    badge: Optional[str] = ""
    buttonText: Optional[str] = ""

