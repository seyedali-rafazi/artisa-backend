"""Transport models using Beanie ODM."""

from datetime import datetime
from typing import Optional, List
from beanie import Document
from pydantic import Field
from enum import Enum


class TransportType(str, Enum):
    """Transport type enumeration."""

    BUS = "bus"
    TRAIN = "train"


class TransportTrip(Document):
    """Transport trip document for bus and train."""

    transport_type: TransportType
    company: str = Field(max_length=100)
    logo: Optional[str] = None
    trip_number: str = Field(max_length=20)
    origin: str = Field(max_length=100)
    destination: str = Field(max_length=100)
    departure_time: datetime
    arrival_time: datetime
    duration: str = Field(max_length=20)
    price: float
    available_seats: int
    features: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "transport_trips"
        indexes = [
            "transport_type",
            "origin",
            "destination",
            "departure_time",
            "is_active",
        ]

    def __str__(self):
        return (
            f"{self.company} {self.trip_number} - {self.origin} to {self.destination}"
        )

    class Config:
        json_schema_extra = {
            "example": {
                "transport_type": "bus",
                "company": "Greyhound",
                "logo": "https://example.com/logo.png",
                "trip_number": "GH001",
                "origin": "New York",
                "destination": "Boston",
                "departure_time": "2024-01-01T10:00:00",
                "arrival_time": "2024-01-01T14:00:00",
                "duration": "4h 0m",
                "price": 50.00,
                "available_seats": 40,
                "features": ["WiFi", "AC", "Restroom"],
                "is_active": True,
            }
        }


class TransportRoute(Document):
    """Popular transport routes for display."""

    transport_type: TransportType
    from_city: str = Field(max_length=100)
    to_city: str = Field(max_length=100)
    price: str = Field(max_length=50)
    image: Optional[str] = None
    is_active: bool = True
    order: int = 0

    class Settings:
        name = "transport_routes"
        indexes = [
            "transport_type",
            "order",
            "is_active",
        ]

    def __str__(self):
        return f"{self.from_city} to {self.to_city} ({self.transport_type})"


# Made with Bob
