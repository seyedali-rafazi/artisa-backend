"""Newsletter API Router — Public Subscription & Admin Management."""

from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from dependencies.permissions import require_admin
from models.newsletter import NewsletterSubscriber
from models.user import User
from schemas.newsletter import (
    NewsletterSubscribeRequest,
    NewsletterSubscriberResponse,
    PaginatedNewsletterSubscribersResponse,
)
from schemas.response import success_response
from services.audit_service import AuditLogService

# Public router
router = APIRouter()
# Admin router
admin_newsletter_router = APIRouter(prefix="/admin/newsletter", tags=["Admin Newsletter"])


def serialize_subscriber(sub: NewsletterSubscriber) -> NewsletterSubscriberResponse:
    """Map NewsletterSubscriber Beanie document to NewsletterSubscriberResponse schema."""
    return NewsletterSubscriberResponse(
        id=str(sub.id),
        email=sub.email,
        is_active=getattr(sub, "is_active", True),
        created_at=getattr(sub, "created_at", None),
        updated_at=getattr(sub, "updated_at", None),
    )


async def get_subscriber_or_404(subscriber_id: str) -> NewsletterSubscriber:
    """Fetch subscriber by ID or raise 404 HTTPException."""
    try:
        sub = await NewsletterSubscriber.get(PydanticObjectId(subscriber_id))
    except Exception:
        sub = None

    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="عضو خبرنامه مورد نظر یافت نشد",
        )
    return sub


# ─── PUBLIC ENDPOINTS ─────────────────────────────────────────────────────────


@router.post(
    "/subscribe",
    status_code=status.HTTP_200_OK,
    summary="Subscribe email to newsletter",
)
@router.post(
    "",
    include_in_schema=False,
    status_code=status.HTTP_200_OK,
)
@router.post(
    "/",
    include_in_schema=False,
    status_code=status.HTTP_200_OK,
)
async def subscribe_newsletter(payload: NewsletterSubscribeRequest):
    """Subscribe a user email to the store newsletter. Handles duplicates and re-activations gracefully."""
    email = payload.email

    existing = await NewsletterSubscriber.find_one(NewsletterSubscriber.email == email)
    if existing:
        if existing.is_active:
            return success_response(
                data=serialize_subscriber(existing).model_dump(),
                message="ایمیل شما قبلاً در خبرنامه گالری آرتیسا ثبت شده است.",
            )
        else:
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            await existing.save()
            return success_response(
                data=serialize_subscriber(existing).model_dump(),
                message="عضویت شما در خبرنامه با موفقیت مجدداً فعال شد.",
            )

    new_sub = NewsletterSubscriber(
        email=email,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await new_sub.insert()

    return success_response(
        data=serialize_subscriber(new_sub).model_dump(),
        message="ایمیل شما با موفقیت در خبرنامه گالری آرتیسا ثبت شد.",
        status_code=status.HTTP_201_CREATED,
    )


# ─── ADMIN ENDPOINTS ──────────────────────────────────────────────────────────


@admin_newsletter_router.get(
    "/subscribers",
    summary="List newsletter subscribers for admin",
)
@admin_newsletter_router.get(
    "/subscribers/",
    include_in_schema=False,
)
async def admin_list_subscribers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search in email address"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    admin_user: User = Depends(require_admin),
):
    """Retrieve paginated newsletter subscribers with search and status filtering."""
    query_filter = {}

    if search and search.strip():
        s = search.strip()
        query_filter["email"] = {"$regex": s, "$options": "i"}

    if is_active is not None:
        query_filter["is_active"] = is_active

    skip = (page - 1) * limit
    query = NewsletterSubscriber.find(query_filter).sort("-created_at")

    total = await query.count()
    subscribers = await query.skip(skip).limit(limit).to_list()
    active_count = await NewsletterSubscriber.find({"is_active": True}).count()

    items = [serialize_subscriber(s).model_dump() for s in subscribers]
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    paginated_data = PaginatedNewsletterSubscribersResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        active_count=active_count,
    ).model_dump()

    return success_response(
        data=paginated_data,
        message="لیست اعضای خبرنامه با موفقیت دریافت شد",
    )


@admin_newsletter_router.patch(
    "/subscribers/{id}/toggle-active",
    summary="Toggle newsletter subscriber active status",
)
async def admin_toggle_subscriber_active(
    id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Toggle newsletter subscriber between active and inactive."""
    sub = await get_subscriber_or_404(id)
    sub.is_active = not sub.is_active
    sub.updated_at = datetime.utcnow()
    await sub.save()

    status_str = "فعال" if sub.is_active else "غیرفعال"
    await AuditLogService.log_action(
        user=admin_user,
        action="TOGGLE_NEWSLETTER_SUBSCRIBER_STATUS",
        resource=f"newsletter_{sub.id}",
        details={"email": sub.email, "is_active": sub.is_active},
        request=request,
    )

    return success_response(
        data=serialize_subscriber(sub).model_dump(),
        message=f"وضعیت عضویت ایمیل {sub.email} به «{status_str}» تغییر یافت",
    )


@admin_newsletter_router.delete(
    "/subscribers/{id}",
    summary="Delete a newsletter subscriber",
)
async def admin_delete_subscriber(
    id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Permanently delete a newsletter subscriber."""
    sub = await get_subscriber_or_404(id)
    sub_id = str(sub.id)
    sub_email = sub.email

    await sub.delete()

    await AuditLogService.log_action(
        user=admin_user,
        action="DELETE_NEWSLETTER_SUBSCRIBER",
        resource=f"newsletter_{sub_id}",
        details={"email": sub_email},
        request=request,
    )

    return success_response(
        data={"id": sub_id},
        message="عضو خبرنامه با موفقیت حذف شد",
    )
