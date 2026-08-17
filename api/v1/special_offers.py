"""Special Offers API Endpoints (Public and Admin)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status

from dependencies.permissions import require_admin
from models.user import User
from schemas.response import success_response, error_response
from schemas.special_offer import (
    SpecialOfferCreate,
    SpecialOfferUpdate,
    SpecialOfferResponse,
    PaginatedSpecialOffersResponse,
)
from services.special_offer_service import SpecialOfferService

public_router = APIRouter(prefix="/special-offers", tags=["Special Offers"])
admin_special_offers_router = APIRouter(prefix="/admin/special-offers", tags=["Admin Special Offers"])


# ─── 1. PUBLIC ENDPOINTS ───────────────────────────────────────────────────


@public_router.get(
    "/active",
    summary="Get currently active special offers for storefront",
)
async def get_active_special_offers():
    """Retrieve all currently active special offers.
    
    Only returns offers satisfying: start_at <= current_time < end_at AND is_active is True.
    """
    active_offers = await SpecialOfferService.get_active_public_offers()
    data = [o.model_dump() for o in active_offers]
    return success_response(
        data=data,
        message="لیست پیشنهادات ویژه فعال با موفقیت دریافت شد",
    )


@public_router.get(
    "/{offer_id}",
    summary="Get single active special offer by ID",
)
async def get_public_special_offer_by_id(offer_id: str):
    """Retrieve single special offer by ID if currently active."""
    offer = await SpecialOfferService.get_offer_by_id(offer_id)
    if offer.status != "active":
        return error_response(
            message="این پیشنهاد ویژه در حال حاضر فعال نمی‌باشد",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return success_response(
        data=offer.model_dump(),
        message="اطلاعات پیشنهاد ویژه دریافت شد",
    )


# ─── 2. ADMIN ENDPOINTS ────────────────────────────────────────────────────


@admin_special_offers_router.get(
    "",
    summary="List special offers with pagination and filtering for admin",
)
async def list_admin_special_offers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    admin_user: User = Depends(require_admin),
):
    """List paginated special offers for admin management."""
    items, total_count, total_pages = await SpecialOfferService.list_admin_offers(
        page=page, limit=limit, search=search, status_filter=status_filter
    )
    result = PaginatedSpecialOffersResponse(
        items=items,
        total=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )
    return success_response(
        data=result.model_dump(),
        message="لیست پیشنهادات ویژه دریافت شد",
    )


@admin_special_offers_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new special offer",
)
async def create_special_offer(
    payload: SpecialOfferCreate,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Create a new scheduled special offer."""
    offer = await SpecialOfferService.create_offer(
        admin_user=admin_user, payload=payload, request=request
    )
    return success_response(
        data=offer.model_dump(),
        message="پیشنهاد ویژه با موفقیت ایجاد گردید",
        status_code=status.HTTP_201_CREATED,
    )


@admin_special_offers_router.get(
    "/{offer_id}",
    summary="Get special offer details for admin",
)
async def get_admin_special_offer(
    offer_id: str,
    admin_user: User = Depends(require_admin),
):
    """Fetch complete special offer details including populated products."""
    offer = await SpecialOfferService.get_offer_by_id(offer_id)
    return success_response(
        data=offer.model_dump(),
        message="اطلاعات پیشنهاد ویژه دریافت شد",
    )


@admin_special_offers_router.put(
    "/{offer_id}",
    summary="Update an existing special offer",
)
async def update_special_offer(
    offer_id: str,
    payload: SpecialOfferUpdate,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Update special offer dates, products, title, or status."""
    offer = await SpecialOfferService.update_offer(
        admin_user=admin_user, offer_id=offer_id, payload=payload, request=request
    )
    return success_response(
        data=offer.model_dump(),
        message="پیشنهاد ویژه با موفقیت بروزرسانی شد",
    )


@admin_special_offers_router.patch(
    "/{offer_id}/toggle-active",
    summary="Toggle active state of a special offer",
)
async def toggle_special_offer_active(
    offer_id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Toggle manual active flag for a special offer."""
    offer = await SpecialOfferService.toggle_active(
        admin_user=admin_user, offer_id=offer_id, request=request
    )
    return success_response(
        data=offer.model_dump(),
        message="وضعیت فعال‌سازی پیشنهاد با موفقیت تغییر کرد",
    )


@admin_special_offers_router.delete(
    "/{offer_id}",
    summary="Delete a special offer",
)
async def delete_special_offer(
    offer_id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Permanently delete a special offer."""
    await SpecialOfferService.delete_offer(
        admin_user=admin_user, offer_id=offer_id, request=request
    )
    return success_response(
        message="پیشنهاد ویژه با موفقیت حذف شد",
    )
