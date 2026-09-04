"""Banner Document Model for Hero Slider & Banner Management."""

from datetime import datetime
from typing import List, Optional
import uuid
from beanie import Document
from pydantic import BaseModel, Field


class BannerPosition(BaseModel):
    """Normalized percentage-based coordinates (0 - 100) for responsive layout."""

    x: float = Field(default=50.0, ge=0.0, le=100.0, description="Horizontal X position percentage (0-100)")
    y: float = Field(default=50.0, ge=0.0, le=100.0, description="Vertical Y position percentage (0-100)")


class BannerTextElement(BaseModel):
    """Draggable text element overlaid on top of a banner image."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(..., min_length=1, max_length=500, description="Text string")
    fontFamily: str = Field(default="inherit", description="Font family name")
    fontSize: int = Field(default=24, ge=8, le=140, description="Base font size in px")
    fontWeight: str = Field(default="normal", description="Font weight (e.g. 400, 500, 600, 700, 800)")
    color: str = Field(default="#FFFFFF", description="Hex or RGBA color code")
    textAlign: str = Field(default="center", description="Text alignment: right, center, left")
    lineHeight: Optional[float] = Field(default=1.4, description="Line height multiplier")
    letterSpacing: Optional[float] = Field(default=0.0, description="Letter spacing in px")
    textShadow: Optional[str] = Field(default=None, description="CSS text-shadow string")
    position: BannerPosition = Field(default_factory=BannerPosition)
    scaleX: Optional[float] = Field(default=1.0, ge=0.1, le=10.0, description="Horizontal scale multiplier")
    scaleY: Optional[float] = Field(default=1.0, ge=0.1, le=10.0, description="Vertical scale multiplier")


class Banner(Document):
    """Hero Slider & Storefront Banner model."""

    title: str = Field(..., min_length=1, max_length=200, description="Banner internal and display title")
    image: str = Field(..., description="Vercel Blob public image URL")
    texts: List[BannerTextElement] = Field(default_factory=list, description="Overlaid typography elements")
    link: Optional[str] = Field(default="", description="Target route or external URL")
    linkOpenInNewTab: bool = Field(default=False, description="Open link in new browser tab")
    isActive: bool = Field(default=True, description="Whether banner is published and active")
    order: int = Field(default=0, description="Display order sequence")

    # Legacy fields maintained for backward compatibility
    subtitle: Optional[str] = Field(default="", description="Legacy subtitle")
    badge: Optional[str] = Field(default="", description="Legacy badge text")
    buttonText: Optional[str] = Field(default="", description="Legacy CTA button text")

    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "banners"

