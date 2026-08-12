"""Order Pydantic Schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    id: str
    quantity: int = Field(gt=0, description="تعداد سفارش باید حداقل ۱ باشد")
    name: Optional[str] = None
    price: Optional[float] = None
    image: Optional[str] = None


class OrderItemSchema(BaseModel):
    id: str
    name: str
    price: float
    quantity: int
    image: str


class ShippingAddressSchema(BaseModel):
    fullName: str
    phone: str
    postalCode: Optional[str] = None
    address: str


class OrderCreate(BaseModel):
    fullName: str
    phone: str
    postalCode: Optional[str] = None
    address: str
    paymentMethod: str = "card"  # online, card
    items: List[OrderItemCreate]


class PaymentRejectPayload(BaseModel):
    rejectionReason: Optional[str] = None


class OrderResponse(BaseModel):
    id: str
    date: str
    status: str
    totalPrice: float
    paymentStatus: str
    paymentMethod: str
    receiptUrl: Optional[str] = None
    rejectionReason: Optional[str] = None
    items: List[OrderItemSchema]
    shippingAddress: Optional[ShippingAddressSchema] = None


class TrackingStep(BaseModel):
    title: str
    desc: str
    completed: bool


class OrderTrackingResponse(BaseModel):
    orderId: str
    status: str
    paymentStatus: str
    date: str
    totalPrice: float
    receiptUrl: Optional[str] = None
    rejectionReason: Optional[str] = None
    steps: List[TrackingStep]

