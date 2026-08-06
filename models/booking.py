"""Booking models using Beanie ODM."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from beanie import Document, Link
from pydantic import Field, EmailStr
from enum import Enum
import random
import string


class BookingType(str, Enum):
    """Booking type enumeration."""

    FLIGHT = "flight"
    BUS = "bus"
    TRAIN = "train"


class BookingStatus(str, Enum):
    """Booking status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Gender(str, Enum):
    """Gender enumeration."""

    MALE = "male"
    FEMALE = "female"


class PassengerInfo(Dict[str, Any]):
    """Passenger information structure."""

    pass


class Booking(Document):
    """Main booking document for flights and transport."""

    user_id: Optional[str] = None  # Reference to User by ID
    booking_type: BookingType

    # Flight or Transport reference by ID
    flight_id: Optional[str] = None
    transport_trip_id: Optional[str] = None

    # Passengers data (stored as list of dicts)
    passengers: List[Dict[str, Any]] = Field(default_factory=list)

    # Contact information
    contact_email: EmailStr
    contact_phone: str = Field(max_length=20)

    # Booking details
    tracking_code: str = Field(unique=True, max_length=20)
    total_price: float
    status: BookingStatus = BookingStatus.PENDING

    # Seat information
    seat_numbers: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "bookings"
        indexes = [
            "tracking_code",
            "user_id",
            "booking_type",
            "status",
            "created_at",
        ]

    def __str__(self):
        return f"{self.tracking_code} - {self.booking_type}"

    @staticmethod
    def generate_tracking_code() -> str:
        """Generate a unique tracking code."""
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "booking_type": "flight",
                "flight_id": "507f1f77bcf86cd799439012",
                "passengers": [
                    {
                        "first_name": "John",
                        "last_name": "Doe",
                        "national_id": "1234567890",
                        "birth_date": "1990-01-01",
                        "gender": "male",
                    }
                ],
                "contact_email": "john@example.com",
                "contact_phone": "+1234567890",
                "tracking_code": "ABC1234567",
                "total_price": 1200.00,
                "status": "pending",
                "seat_numbers": ["12A", "12B"],
            }
        }


# Made with Bob
