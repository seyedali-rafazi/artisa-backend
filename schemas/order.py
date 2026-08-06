"""Order Pydantic Schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


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
    paymentMethod: str = "online"  # online, card
    items: List[OrderItemSchema]


class OrderResponse(BaseModel):
    id: str
    date: str
    status: str
    totalPrice: float
    paymentStatus: str
    paymentMethod: str
    items: List[OrderItemSchema]
    shippingAddress: Optional[ShippingAddressSchema] = None


class TrackingStep(BaseModel):
    title: str
    desc: str
    completed: bool


class OrderTrackingResponse(BaseModel):
    orderId: str
    status: str
    date: str
    totalPrice: float
    steps: List[TrackingStep]
