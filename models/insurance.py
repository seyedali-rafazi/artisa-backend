"""Insurance models using Beanie ODM."""

from datetime import datetime
from typing import Optional, List
from beanie import Document
from pydantic import Field, EmailStr
from enum import Enum


class InsuranceStatus(str, Enum):
    """Insurance booking status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Insurance(Document):
    """Insurance plan document."""

    title: str = Field(max_length=200)
    price: float
    coverage: str = Field(max_length=200)
    popular: bool = False
    features: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "insurance_plans"
        indexes = [
            "popular",
            "is_active",
            "price",
        ]

    def __str__(self):
        return self.title

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Travel Insurance Basic",
                "price": 50.00,
                "coverage": "Up to $50,000",
                "popular": False,
                "features": ["Medical coverage", "Trip cancellation", "Lost baggage"],
                "is_active": True,
            }
        }


class InsuranceBooking(Document):
    """Insurance booking document."""

    plan_id: str  # Reference to Insurance by ID
    user_id: Optional[str] = None  # Reference to User by ID

    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    national_id: str = Field(max_length=20)
    birth_date: str = Field(max_length=20)   # ISO string YYYY-MM-DD
    destination: str = Field(max_length=200)
    start_date: str = Field(max_length=20)   # ISO string YYYY-MM-DD
    end_date: str = Field(max_length=20)     # ISO string YYYY-MM-DD
    phone: str = Field(max_length=20)
    email: EmailStr

    tracking_code: str = Field(unique=True, max_length=20)
    status: InsuranceStatus = InsuranceStatus.PENDING

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "insurance_bookings"
        indexes = [
            "tracking_code",
            "user_id",
            "plan_id",
            "status",
            "created_at",
        ]

    def __str__(self):
        return f"{self.tracking_code} - {self.first_name} {self.last_name}"

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "507f1f77bcf86cd799439011",
                "user_id": "507f1f77bcf86cd799439012",
                "first_name": "John",
                "last_name": "Doe",
                "national_id": "1234567890",
                "birth_date": "1990-01-01",
                "destination": "Paris, France",
                "start_date": "2024-06-01",
                "end_date": "2024-06-15",
                "phone": "+1234567890",
                "email": "john@example.com",
                "tracking_code": "INS1234567",
                "status": "pending",
            }
        }


# Made with Bob
