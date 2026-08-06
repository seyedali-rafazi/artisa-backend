"""Flight models using Beanie ODM."""

from datetime import datetime
from typing import Optional, List
from beanie import Document
from pydantic import Field
from enum import Enum


class FlightClass(str, Enum):
    """Flight class enumeration."""

    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST = "first"


class City(Document):
    """City document model for flight origins and destinations."""

    code: str = Field(unique=True, index=True, max_length=10)
    name: str = Field(max_length=100)
    country: Optional[str] = Field(None, max_length=100)

    class Settings:
        name = "cities"
        indexes = [
            "code",
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Flight(Document):
    """Flight document model for storing flight information."""

    airline: str = Field(max_length=100)
    logo: Optional[str] = None
    flight_number: str = Field(max_length=20)
    origin: str = Field(max_length=10)
    destination: str = Field(max_length=10)
    departure_time: datetime
    arrival_time: datetime
    duration: str = Field(max_length=20)
    price: float
    available_seats: int
    stops: int = 0
    flight_class: FlightClass = FlightClass.ECONOMY
    features: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "flights"
        indexes = [
            "origin",
            "destination",
            "departure_time",
            "flight_class",
            "is_active",
        ]

    def __str__(self):
        return (
            f"{self.airline} {self.flight_number} - {self.origin} to {self.destination}"
        )

    class Config:
        json_schema_extra = {
            "example": {
                "airline": "Emirates",
                "logo": "https://example.com/logo.png",
                "flight_number": "EK001",
                "origin": "DXB",
                "destination": "JFK",
                "departure_time": "2024-01-01T10:00:00",
                "arrival_time": "2024-01-01T18:00:00",
                "duration": "8h 0m",
                "price": 1200.00,
                "available_seats": 150,
                "stops": 0,
                "flight_class": "economy",
                "features": ["WiFi", "Meals", "Entertainment"],
                "is_active": True,
            }
        }


class PopularFlight(Document):
    """Popular flight routes for homepage display."""

    from_city: str = Field(max_length=100)
    to_city: str = Field(max_length=100)
    from_code: str = Field(max_length=10)
    to_code: str = Field(max_length=10)
    price: str = Field(max_length=50)
    image: Optional[str] = None
    is_active: bool = True
    order: int = 0

    class Settings:
        name = "popular_flights"
        indexes = [
            "order",
            "is_active",
        ]

    def __str__(self):
        return f"{self.from_city} to {self.to_city}"


class Destination(Document):
    """Popular destinations for homepage display."""

    title: str = Field(max_length=100)
    subtitle: str = Field(max_length=200)
    image: str
    destination_code: str = Field(max_length=10)
    is_active: bool = True
    order: int = 0

    class Settings:
        name = "destinations"
        indexes = [
            "order",
            "is_active",
        ]

    def __str__(self):
        return self.title


# Made with Bob
