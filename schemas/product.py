"""Product Pydantic Schemas."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str
    nameEn: str = ""
    price: float = Field(..., gt=0)
    oldPrice: Optional[float] = None
    image: str
    category: str
    categoryEn: str = ""
    rating: float = 5.0
    isSpecial: bool = False
    isBestSeller: bool = False
    description: Optional[str] = None
    descriptionEn: Optional[str] = None
    specifications: Dict[str, str] = Field(default_factory=dict)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    nameEn: Optional[str] = None
    price: Optional[float] = None
    oldPrice: Optional[float] = None
    image: Optional[str] = None
    category: Optional[str] = None
    categoryEn: Optional[str] = None
    rating: Optional[float] = None
    isSpecial: Optional[bool] = None
    isBestSeller: Optional[bool] = None
    description: Optional[str] = None
    descriptionEn: Optional[str] = None
    specifications: Optional[Dict[str, str]] = None


class ProductResponse(BaseModel):
    id: str
    name: str
    nameEn: str
    price: float
    oldPrice: Optional[float] = None
    image: str
    category: str
    categoryEn: str
    rating: float
    isSpecial: Optional[bool] = False
    isBestSeller: Optional[bool] = False
    description: Optional[str] = None
    descriptionEn: Optional[str] = None
    specifications: Optional[Dict[str, str]] = Field(default_factory=dict)


class ProductPaginatedResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    limit: int
    total_pages: int
