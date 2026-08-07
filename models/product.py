"""Product Document Model."""

from datetime import datetime
from typing import Dict, List, Optional
from beanie import Document, Indexed
from pydantic import Field


class Product(Document):
    """Product MongoDB model."""

    name: str
    nameEn: str = ""
    price: float
    oldPrice: Optional[float] = None
    image: str
    gallery: List[str] = Field(default_factory=list)
    category: Indexed(str)  # type: ignore
    categoryEn: str = ""
    rating: float = 5.0
    isSpecial: bool = False
    isBestSeller: bool = False
    description: Optional[str] = None
    descriptionEn: Optional[str] = None
    specifications: Dict[str, str] = Field(default_factory=dict)
    stock_quantity: int = 100
    sku: Optional[str] = None
    status: str = "published"  # "published", "draft", "archived"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "products"

    class Config:
        json_schema_extra = {
            "example": {
                "name": "تابلو نقاشی رنگ‌روغن «افق طلایی»",
                "nameEn": "Golden Horizon Oil Painting",
                "price": 3200000,
                "oldPrice": 4500000,
                "image": "https://images.unsplash.com/photo-1578301978693-85fa9c0320b9",
                "gallery": [],
                "category": "تابلو نقاشی",
                "categoryEn": "Painting",
                "rating": 4.9,
                "isSpecial": True,
                "isBestSeller": False,
                "description": "تابلو رنگ‌روغن دست‌ساز با تکنیک پالت‌نایف...",
                "specifications": {
                    "تکنیک": "رنگ‌روغن روی بوم کتان",
                    "ابعاد": "۸۰ × ۶۰ سانتی‌متر"
                },
                "stock_quantity": 10,
                "status": "published"
            }
        }
