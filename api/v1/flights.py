"""Flight API endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Query
from beanie import PydanticObjectId
from models.flight import Flight, City, PopularFlight, Destination


router = APIRouter()


@router.get("/search")
async def search_flights(
    origin: str = Query(..., description="Origin city code"),
    destination: str = Query(..., description="Destination city code"),
    departure_date: Optional[str] = Query(
        None, description="Departure date (YYYY-MM-DD)"
    ),
    flight_class: Optional[str] = Query("economy", description="Flight class"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search for flights."""
    query = Flight.find(
        Flight.origin == origin,
        Flight.destination == destination,
        Flight.is_active == True,
    )

    if flight_class:
        query = query.find(Flight.flight_class == flight_class)

    flights = await query.limit(limit).to_list()
    return flights


@router.get("/{flight_id}")
async def get_flight(flight_id: str):
    """Get flight by ID."""
    try:
        flight = await Flight.get(PydanticObjectId(flight_id))
        if not flight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found"
            )
        return flight
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid flight ID"
        )


@router.get("/popular/routes")
async def get_popular_flights():
    """Get popular flight routes."""
    popular = (
        await PopularFlight.find(PopularFlight.is_active == True)
        .sort("+order")
        .to_list()
    )
    return popular


@router.get("/destinations/popular")
async def get_popular_destinations():
    """Get popular destinations."""
    destinations = (
        await Destination.find(Destination.is_active == True).sort("+order").to_list()
    )
    return destinations


@router.get("/cities/search")
async def search_cities(q: str = Query(..., min_length=2)):
    """Search cities by name or code."""
    cities = (
        await City.find(
            {
                "$or": [
                    {"name": {"$regex": q, "$options": "i"}},
                    {"code": {"$regex": q, "$options": "i"}},
                ]
            }
        )
        .limit(10)
        .to_list()
    )
    return cities


@router.get("/cities/all")
async def get_all_cities():
    """Get all cities."""
    cities = await City.find_all().to_list()
    return cities


# Made with Bob
