"""Order Document Model."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from beanie import Document, Indexed
from pydantic import Field, BaseModel


class OrderItem(BaseModel):
    id: str
    name: str
    price: float
    quantity: int
    image: str


class ShippingAddress(BaseModel):
    fullName: str
    phone: str
    postalCode: Optional[str] = None
    address: str


class Order(Document):
    """Order document model."""

    orderId: Indexed(str, unique=True)  # type: ignore e.g. "ORD-10042" or "654321"
    userId: Optional[str] = None
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y/%m/%d"))
    status: str = "pending"  # pending, processing, shipped, delivered, cancelled, completed
    totalPrice: float
    paymentStatus: str = "pending_payment"  # pending_payment, payment_pending_review, payment_approved, payment_rejected
    paymentMethod: str = "card"  # card, online
    receiptUrl: Optional[str] = None
    rejectionReason: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    items: List[OrderItem] = Field(default_factory=list)
    shippingAddress: Optional[ShippingAddress] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "orders"

