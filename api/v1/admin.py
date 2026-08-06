"""
Admin API endpoints — protected by X-Admin-Key header.

The header value must equal SECRET_KEY from your .env file.

Seeding
  POST   /api/v1/admin/seed               — auto-generate data for N days
  DELETE /api/v1/admin/seed/future        — wipe future auto-generated data
  GET    /api/v1/admin/seed/status        — record counts per collection

Flights (manual CRUD)
  POST   /api/v1/admin/flights            — create a flight
  GET    /api/v1/admin/flights            — list all flights (paginated)
  PUT    /api/v1/admin/flights/{id}       — update a flight
  DELETE /api/v1/admin/flights/{id}       — delete a flight

Transport trips (manual CRUD)
  POST   /api/v1/admin/transport          — create a bus/train trip
  GET    /api/v1/admin/transport          — list all trips (paginated)
  PUT    /api/v1/admin/transport/{id}     — update a trip
  DELETE /api/v1/admin/transport/{id}     — delete a trip

Insurance plans (manual CRUD)
  POST   /api/v1/admin/insurance/plans            — create a plan
  GET    /api/v1/admin/insurance/plans            — list all plans
  PUT    /api/v1/admin/insurance/plans/{id}       — update a plan
  DELETE /api/v1/admin/insurance/plans/{id}       — delete a plan
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from beanie import PydanticObjectId
from core.config import settings
from core.seeder import clean_future_data, run_full_seed
from fastapi import APIRouter, Header, HTTPException, Query, status
from models.flight import City, Flight, FlightClass, PopularFlight
from models.insurance import Insurance
from models.transport import TransportRoute, TransportTrip, TransportType
from pydantic import BaseModel, Field

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Auth helper
# ─────────────────────────────────────────────────────────────────────────────


def _require_admin_key(key: Optional[str]) -> None:
    if not key or not secrets.compare_digest(key, settings.SECRET_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-Admin-Key header",
        )


def _not_found(label: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found"
    )


def _bad_id(label: str):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {label} ID"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Request schemas
# ─────────────────────────────────────────────────────────────────────────────


class SeedRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=30)
    trips_per_pair: int = Field(default=3, ge=1, le=10)
    clean: bool = False


class FlightCreate(BaseModel):
    airline: str
    logo: Optional[str] = None
    flight_number: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    duration: str
    price: float
    available_seats: int
    stops: int = 0
    flight_class: FlightClass = FlightClass.ECONOMY
    features: List[str] = []
    is_active: bool = True


class FlightUpdate(BaseModel):
    airline: Optional[str] = None
    logo: Optional[str] = None
    flight_number: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    duration: Optional[str] = None
    price: Optional[float] = None
    available_seats: Optional[int] = None
    stops: Optional[int] = None
    flight_class: Optional[FlightClass] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TransportCreate(BaseModel):
    transport_type: TransportType
    company: str
    logo: Optional[str] = None
    trip_number: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    duration: str
    price: float
    available_seats: int
    features: List[str] = []
    is_active: bool = True


class TransportUpdate(BaseModel):
    transport_type: Optional[TransportType] = None
    company: Optional[str] = None
    logo: Optional[str] = None
    trip_number: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    duration: Optional[str] = None
    price: Optional[float] = None
    available_seats: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None


class InsurancePlanCreate(BaseModel):
    title: str
    price: float
    coverage: str
    popular: bool = False
    features: List[str] = []
    is_active: bool = True


class InsurancePlanUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
    coverage: Optional[str] = None
    popular: Optional[bool] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None


# ─────────────────────────────────────────────────────────────────────────────
# Seeding endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/seed", status_code=status.HTTP_200_OK, tags=["admin"])
async def seed_data(
    body: SeedRequest = SeedRequest(),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Auto-generate flights, buses and trains for all city permutations."""
    _require_admin_key(x_admin_key)
    started_at = datetime.utcnow()
    result = await run_full_seed(
        days=body.days, trips_per_pair=body.trips_per_pair, clean=body.clean
    )
    elapsed = (datetime.utcnow() - started_at).total_seconds()
    return {"success": True, "elapsed_seconds": round(elapsed, 2), "summary": result}


@router.delete("/seed/future", status_code=status.HTTP_200_OK, tags=["admin"])
async def delete_future_data(
    days: int = 7,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Delete auto-generated flights/trips for the next N days."""
    _require_admin_key(x_admin_key)
    result = await clean_future_data(days)
    return {"success": True, "deleted": result}


@router.get("/seed/status", status_code=status.HTTP_200_OK, tags=["admin"])
async def seed_status(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Return record counts per collection."""
    _require_admin_key(x_admin_key)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    future = today + timedelta(days=7)
    return {
        "cities": await City.find_all().count(),
        "popular_flights": await PopularFlight.find_all().count(),
        "popular_transport_routes": await TransportRoute.find_all().count(),
        "flights_total": await Flight.find_all().count(),
        "flights_next_7_days": await Flight.find(
            Flight.departure_time >= today, Flight.departure_time < future
        ).count(),
        "transport_trips_total": await TransportTrip.find_all().count(),
        "transport_trips_next_7_days": await TransportTrip.find(
            TransportTrip.departure_time >= today, TransportTrip.departure_time < future
        ).count(),
        "insurance_plans": await Insurance.find_all().count(),
        "checked_at": today.isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Flight CRUD
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/flights", status_code=status.HTTP_201_CREATED, tags=["admin-flights"])
async def create_flight(
    body: FlightCreate,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Create a single flight record."""
    _require_admin_key(x_admin_key)
    flight = Flight(**body.model_dump())
    await flight.insert()
    return flight


@router.get("/flights", status_code=status.HTTP_200_OK, tags=["admin-flights"])
async def list_flights(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    origin: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """List all flights with optional origin/destination filter."""
    _require_admin_key(x_admin_key)
    query = Flight.find()
    if origin:
        query = query.find(Flight.origin == origin)
    if destination:
        query = query.find(Flight.destination == destination)
    flights = await query.skip(skip).limit(limit).to_list()
    total = await Flight.find().count()
    return {"total": total, "skip": skip, "limit": limit, "results": flights}


@router.put(
    "/flights/{flight_id}", status_code=status.HTTP_200_OK, tags=["admin-flights"]
)
async def update_flight(
    flight_id: str,
    body: FlightUpdate,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Update any field of a flight by ID."""
    _require_admin_key(x_admin_key)
    try:
        flight = await Flight.get(PydanticObjectId(flight_id))
    except Exception:
        _bad_id("flight")
    if not flight:
        _not_found("Flight")

    updates = body.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(flight, field, value)
    flight.updated_at = datetime.utcnow()
    await flight.save()
    return flight


@router.delete(
    "/flights/{flight_id}", status_code=status.HTTP_200_OK, tags=["admin-flights"]
)
async def delete_flight(
    flight_id: str,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Permanently delete a flight by ID."""
    _require_admin_key(x_admin_key)
    try:
        flight = await Flight.get(PydanticObjectId(flight_id))
    except Exception:
        _bad_id("flight")
    if not flight:
        _not_found("Flight")
    await flight.delete()
    return {"success": True, "deleted_id": flight_id}


# ─────────────────────────────────────────────────────────────────────────────
# Transport (Bus / Train) CRUD
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/transport", status_code=status.HTTP_201_CREATED, tags=["admin-transport"]
)
async def create_transport_trip(
    body: TransportCreate,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Create a single bus or train trip."""
    _require_admin_key(x_admin_key)
    trip = TransportTrip(**body.model_dump())
    await trip.insert()
    return trip


@router.get("/transport", status_code=status.HTTP_200_OK, tags=["admin-transport"])
async def list_transport_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    transport_type: Optional[str] = Query(None, description="bus or train"),
    origin: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """List all transport trips with optional filters."""
    _require_admin_key(x_admin_key)
    query = TransportTrip.find()
    if transport_type:
        query = query.find(TransportTrip.transport_type == transport_type)
    if origin:
        query = query.find(TransportTrip.origin == origin)
    if destination:
        query = query.find(TransportTrip.destination == destination)
    trips = await query.skip(skip).limit(limit).to_list()
    total = await TransportTrip.find().count()
    return {"total": total, "skip": skip, "limit": limit, "results": trips}


@router.put(
    "/transport/{trip_id}", status_code=status.HTTP_200_OK, tags=["admin-transport"]
)
async def update_transport_trip(
    trip_id: str,
    body: TransportUpdate,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Update any field of a transport trip by ID."""
    _require_admin_key(x_admin_key)
    try:
        trip = await TransportTrip.get(PydanticObjectId(trip_id))
    except Exception:
        _bad_id("trip")
    if not trip:
        _not_found("Transport trip")

    updates = body.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(trip, field, value)
    trip.updated_at = datetime.utcnow()
    await trip.save()
    return trip


@router.delete(
    "/transport/{trip_id}", status_code=status.HTTP_200_OK, tags=["admin-transport"]
)
async def delete_transport_trip(
    trip_id: str,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Permanently delete a transport trip by ID."""
    _require_admin_key(x_admin_key)
    try:
        trip = await TransportTrip.get(PydanticObjectId(trip_id))
    except Exception:
        _bad_id("trip")
    if not trip:
        _not_found("Transport trip")
    await trip.delete()
    return {"success": True, "deleted_id": trip_id}


# ─────────────────────────────────────────────────────────────────────────────
# Insurance plan CRUD
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/insurance/plans", status_code=status.HTTP_201_CREATED, tags=["admin-insurance"]
)
async def create_insurance_plan(
    body: InsurancePlanCreate,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Create a new insurance plan."""
    _require_admin_key(x_admin_key)
    plan = Insurance(**body.model_dump())
    await plan.insert()
    return plan


@router.get(
    "/insurance/plans", status_code=status.HTTP_200_OK, tags=["admin-insurance"]
)
async def list_insurance_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """List all insurance plans (including inactive)."""
    _require_admin_key(x_admin_key)
    plans = await Insurance.find().skip(skip).limit(limit).to_list()
    total = await Insurance.find().count()
    return {"total": total, "skip": skip, "limit": limit, "results": plans}


@router.put(
    "/insurance/plans/{plan_id}",
    status_code=status.HTTP_200_OK,
    tags=["admin-insurance"],
)
async def update_insurance_plan(
    plan_id: str,
    body: InsurancePlanUpdate,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Update any field of an insurance plan by ID."""
    _require_admin_key(x_admin_key)
    try:
        plan = await Insurance.get(PydanticObjectId(plan_id))
    except Exception:
        _bad_id("plan")
    if not plan:
        _not_found("Insurance plan")

    updates = body.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(plan, field, value)
    plan.updated_at = datetime.utcnow()
    await plan.save()
    return plan


@router.delete(
    "/insurance/plans/{plan_id}",
    status_code=status.HTTP_200_OK,
    tags=["admin-insurance"],
)
async def delete_insurance_plan(
    plan_id: str,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Permanently delete an insurance plan by ID."""
    _require_admin_key(x_admin_key)
    try:
        plan = await Insurance.get(PydanticObjectId(plan_id))
    except Exception:
        _bad_id("plan")
    if not plan:
        _not_found("Insurance plan")
    await plan.delete()
    return {"success": True, "deleted_id": plan_id}


# Made with Bob
