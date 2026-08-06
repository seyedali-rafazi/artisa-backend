"""Booking API endpoints."""

from typing import List, Optional

from beanie import PydanticObjectId
from core.security import get_current_active_user, get_optional_user, verify_csrf
from fastapi import APIRouter, Depends, HTTPException, status
from models.booking import Booking
from models.user import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: dict,
    current_user: Optional[User] = Depends(get_optional_user),
    _csrf: None = Depends(verify_csrf),
):
    """Create a new booking."""
    # Generate tracking code
    tracking_code = Booking.generate_tracking_code()

    # Create booking
    booking = Booking(
        user_id=str(current_user.id) if current_user else None,
        booking_type=booking_data.get("booking_type"),
        flight_id=booking_data.get("flight_id"),
        transport_trip_id=booking_data.get("transport_trip_id"),
        passengers=booking_data.get("passengers", []),
        contact_email=booking_data.get("contact_email"),
        contact_phone=booking_data.get("contact_phone"),
        tracking_code=tracking_code,
        total_price=booking_data.get("total_price"),
        seat_numbers=booking_data.get("seat_numbers", []),
    )

    await booking.insert()
    return booking


@router.get("/my-bookings")
async def get_my_bookings(current_user: User = Depends(get_current_active_user)):
    """Get current user's bookings."""
    bookings = (
        await Booking.find({"user_id": str(current_user.id)})
        .sort("-created_at")
        .to_list()
    )
    return bookings


@router.get("/track/{tracking_code}")
async def track_booking(tracking_code: str):
    """Track booking by tracking code."""
    booking = await Booking.find_one({"tracking_code": tracking_code})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    return booking


@router.get("/{booking_id}")
async def get_booking(
    booking_id: str, current_user: User = Depends(get_current_active_user)
):
    """Get booking by ID."""
    try:
        booking = await Booking.get(PydanticObjectId(booking_id))
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
            )

        # Check if user owns this booking
        if booking.user_id != str(current_user.id) and not current_user.is_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this booking",
            )

        return booking
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking ID"
        )


@router.put("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    current_user: User = Depends(get_current_active_user),
    _csrf: None = Depends(verify_csrf),
):
    """Cancel a booking."""
    try:
        booking = await Booking.get(PydanticObjectId(booking_id))
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
            )

        # Check if user owns this booking
        if booking.user_id != str(current_user.id) and not current_user.is_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this booking",
            )

        booking.status = "cancelled"
        await booking.save()

        return {"message": "Booking cancelled successfully", "booking": booking}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Made with Bob
