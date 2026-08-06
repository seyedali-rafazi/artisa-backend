"""Insurance API endpoints."""

import random
import string
from typing import Optional

from beanie import PydanticObjectId
from core.security import get_current_active_user, get_optional_user, verify_csrf
from fastapi import APIRouter, Depends, HTTPException, status
from models.insurance import Insurance, InsuranceBooking, InsuranceStatus
from models.user import User
from pydantic import BaseModel, EmailStr

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────


class InsuranceBookingCreate(BaseModel):
    plan_id: str
    first_name: str
    last_name: str
    national_id: str
    birth_date: str  # ISO string YYYY-MM-DD
    destination: str
    start_date: str  # ISO string YYYY-MM-DD
    end_date: str  # ISO string YYYY-MM-DD
    phone: str
    email: EmailStr


class InsuranceBookingResponse(BaseModel):
    """Typed response returned after creating an insurance booking."""

    id: str
    tracking_code: str
    status: str
    plan_id: str
    plan_title: str
    plan_price: float
    plan_coverage: str
    first_name: str
    last_name: str
    destination: str
    start_date: str
    end_date: str
    created_at: str


# ─── Plans ────────────────────────────────────────────────────────────────────


@router.get("/plans")
async def get_insurance_plans():
    """Get all active insurance plans."""
    plans = (
        await Insurance.find(Insurance.is_active == True)
        .sort([("popular", -1), ("price", 1)])
        .to_list()
    )
    return plans


@router.get("/plans/{plan_id}")
async def get_insurance_plan(plan_id: str):
    """Get insurance plan by ID."""
    try:
        plan = await Insurance.get(PydanticObjectId(plan_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan ID"
        )
    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Insurance plan not found"
        )
    return plan


# ─── Bookings ─────────────────────────────────────────────────────────────────


@router.post(
    "/bookings",
    status_code=status.HTTP_201_CREATED,
    response_model=InsuranceBookingResponse,
)
async def create_insurance_booking(
    data: InsuranceBookingCreate,
    current_user: Optional[User] = Depends(get_optional_user),
    _csrf: None = Depends(verify_csrf),
):
    """
    Create a new insurance booking.

    Validates that the requested plan exists, generates a tracking code,
    persists the booking with status=confirmed, and returns the full record
    (including tracking_code) so the frontend can redirect to the success page.

    Works for both guests (no Authorization header) and authenticated users.
    """
    # Validate plan exists
    try:
        plan = await Insurance.get(PydanticObjectId(data.plan_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan ID"
        )
    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Insurance plan not found"
        )

    # Validate date range (string comparison works for ISO dates YYYY-MM-DD)
    if data.end_date < data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be on or after start_date",
        )

    # Generate unique tracking code (retry on collision).
    # Use raw dict query to avoid Beanie class-attribute access issues on some
    # deployment environments (e.g. Vercel with older Beanie versions).
    tracking_code = ""
    for _ in range(5):
        tracking_code = "INS" + "".join(
            random.choices(string.ascii_uppercase + string.digits, k=7)
        )
        existing = await InsuranceBooking.find_one({"tracking_code": tracking_code})
        if not existing:
            break

    booking = InsuranceBooking(
        plan_id=str(plan.id),
        user_id=str(current_user.id) if current_user else None,
        first_name=data.first_name,
        last_name=data.last_name,
        national_id=data.national_id,
        birth_date=data.birth_date,
        destination=data.destination,
        start_date=data.start_date,
        end_date=data.end_date,
        phone=data.phone,
        email=data.email,
        tracking_code=tracking_code,
        status=InsuranceStatus.CONFIRMED,
    )

    await booking.insert()

    return InsuranceBookingResponse(
        id=str(booking.id),
        tracking_code=booking.tracking_code,
        status=booking.status.value,
        plan_id=str(plan.id),
        plan_title=plan.title,
        plan_price=plan.price,
        plan_coverage=plan.coverage,
        first_name=booking.first_name,
        last_name=booking.last_name,
        destination=booking.destination,
        start_date=booking.start_date,
        end_date=booking.end_date,
        created_at=booking.created_at.isoformat(),
    )


@router.get("/bookings/my-bookings")
async def get_my_insurance_bookings(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's insurance bookings."""
    bookings = (
        await InsuranceBooking.find({"user_id": str(current_user.id)})
        .sort("-created_at")
        .to_list()
    )
    return bookings


@router.get("/bookings/track/{tracking_code}")
async def track_insurance_booking(tracking_code: str):
    """Track insurance booking by tracking code."""
    booking = await InsuranceBooking.find_one({"tracking_code": tracking_code})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Insurance booking not found"
        )
    return booking


@router.get("/bookings/{booking_id}")
async def get_insurance_booking(
    booking_id: str, current_user: User = Depends(get_current_active_user)
):
    """Get insurance booking by ID."""
    try:
        booking = await InsuranceBooking.get(PydanticObjectId(booking_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking ID"
        )
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance booking not found",
        )

    if booking.user_id != str(current_user.id) and not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this booking",
        )

    return booking


# Made with Bob
