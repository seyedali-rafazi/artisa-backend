"""Pydantic v2 Schemas for Admin Dashboard & Management."""

from datetime import datetime
from typing import List, Dict, Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field, EmailStr

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    total_pages: int


class DashboardStatsResponse(BaseModel):
    total_revenue: float
    today_revenue: float
    monthly_revenue: float
    total_orders: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    total_customers: int
    total_products: int
    low_stock_products: int
    out_of_stock_products: int
    monthly_revenue_chart: List[Dict[str, Any]]
    monthly_orders_chart: List[Dict[str, Any]]
    categories_distribution: List[Dict[str, Any]]
    best_selling_products: List[Dict[str, Any]]


class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    nameEn: str = ""
    price: float = Field(..., gt=0)
    oldPrice: Optional[float] = None
    image: str
    gallery: List[str] = Field(default_factory=list)
    category: str
    categoryEn: str = ""
    rating: float = 5.0
    isSpecial: bool = False
    isBestSeller: bool = False
    description: Optional[str] = None
    descriptionEn: Optional[str] = None
    specifications: Dict[str, str] = Field(default_factory=dict)
    stock_quantity: int = Field(default=100, ge=0)
    sku: Optional[str] = None
    status: str = Field(default="published")  # published, draft, archived


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    nameEn: Optional[str] = None
    price: Optional[float] = None
    oldPrice: Optional[float] = None
    image: Optional[str] = None
    gallery: Optional[List[str]] = None
    category: Optional[str] = None
    categoryEn: Optional[str] = None
    rating: Optional[float] = None
    isSpecial: Optional[bool] = None
    isBestSeller: Optional[bool] = None
    description: Optional[str] = None
    descriptionEn: Optional[str] = None
    specifications: Optional[Dict[str, str]] = None
    stock_quantity: Optional[int] = None
    sku: Optional[str] = None
    status: Optional[str] = None


class UserAdminResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    total_orders: int = 0
    total_spent: float = 0.0
    created_at: datetime
    updated_at: datetime


class UserStatusUpdateRequest(BaseModel):
    is_active: bool


class UserRoleUpdateRequest(BaseModel):
    role: str  # customer, admin, super_admin


class OrderStatusUpdateRequest(BaseModel):
    status: str  # pending, paid, processing, shipped, delivered, cancelled, refunded
    paymentStatus: Optional[str] = None


class AdminCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(default="admin")  # admin or super_admin
    phone: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    user_email: str
    user_role: str
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
