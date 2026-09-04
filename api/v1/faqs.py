"""FAQ Router — Public & Admin Endpoints."""

from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from dependencies.permissions import require_admin
from models.faq import FAQ
from models.user import User
from schemas.faq import (
    FAQCreateRequest,
    FAQReorderRequest,
    FAQResponse,
    FAQUpdateRequest,
)
from schemas.response import error_response, success_response
from services.audit_service import AuditLogService

router = APIRouter()
admin_faqs_router = APIRouter(prefix="/admin/faqs", tags=["Admin FAQs"])


def serialize_faq(f: FAQ) -> FAQResponse:
    """Map FAQ Beanie document to FAQResponse schema with dual field names for backward compatibility."""
    return FAQResponse(
        id=str(f.id),
        question=f.question,
        answer=f.answer,
        q=f.question,
        a=f.answer,
        order=getattr(f, "order", 0) or 0,
        is_active=getattr(f, "is_active", True) if getattr(f, "is_active", None) is not None else True,
        created_at=getattr(f, "created_at", None),
        updated_at=getattr(f, "updated_at", None),
    )


async def get_faq_or_404(faq_id: str) -> FAQ:
    """Fetch FAQ by string ID or raise 404 HTTPException."""
    try:
        faq = await FAQ.get(PydanticObjectId(faq_id))
    except Exception:
        faq = None

    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="سوال متداول مورد نظر یافت نشد",
        )
    return faq


# ─── PUBLIC ENDPOINTS ─────────────────────────────────────────────────────────


@router.get("", summary="Get FAQ list for storefront")
@router.get("/", include_in_schema=False)
async def list_faqs():
    """Retrieve list of active frequently asked questions sorted by display order."""
    # Retrieve active FAQs (support legacy documents where is_active might not be set)
    query_filter = {
        "$or": [
            {"is_active": True},
            {"is_active": {"$exists": False}},
        ]
    }
    faqs = await FAQ.find(query_filter).sort("+order", "+_id").to_list()

    items = [serialize_faq(f).model_dump() for f in faqs]
    return success_response(data=items, message="سوالات متداول دریافت شد")


@router.get("/{id}", summary="Get single FAQ item")
async def get_faq(id: str):
    """Retrieve single public FAQ item by ID."""
    faq = await get_faq_or_404(id)
    if getattr(faq, "is_active", True) is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="سوال متداول مورد نظر یافت نشد",
        )
    return success_response(
        data=serialize_faq(faq).model_dump(),
        message="اطلاعات سوال متداول دریافت شد",
    )


# ─── ADMIN ENDPOINTS ──────────────────────────────────────────────────────────


@admin_faqs_router.get("", summary="List all FAQs for admin management")
@admin_faqs_router.get("/", include_in_schema=False)
async def admin_list_faqs(
    search: Optional[str] = Query(None, description="Search in question or answer"),
    admin_user: User = Depends(require_admin),
):
    """Retrieve all FAQ items (active and inactive) with optional search filter."""
    query_filter = {}
    if search and search.strip():
        s = search.strip()
        query_filter = {
            "$or": [
                {"question": {"$regex": s, "$options": "i"}},
                {"answer": {"$regex": s, "$options": "i"}},
            ]
        }

    faqs = await FAQ.find(query_filter).sort("+order", "+_id").to_list()
    items = [serialize_faq(f).model_dump() for f in faqs]

    return success_response(
        data=items,
        message="لیست مدیریت سوالات متداول با موفقیت دریافت شد",
    )


@admin_faqs_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new FAQ item",
)
@admin_faqs_router.post("/", include_in_schema=False, status_code=status.HTTP_201_CREATED)
async def admin_create_faq(
    payload: FAQCreateRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Create a new FAQ item with order and active status."""
    order_val = payload.order
    if order_val is None or order_val == 0:
        # Default order to next position
        count = await FAQ.count()
        order_val = count + 1

    faq = FAQ(
        question=payload.question.strip(),
        answer=payload.answer.strip(),
        order=order_val,
        is_active=payload.is_active if payload.is_active is not None else True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await faq.insert()

    await AuditLogService.log_action(
        user=admin_user,
        action="CREATE_FAQ",
        resource=f"faq_{faq.id}",
        details={"question": faq.question, "order": faq.order},
        request=request,
    )

    return success_response(
        data=serialize_faq(faq).model_dump(),
        message="سوال متداول جدید با موفقیت ایجاد شد",
        status_code=status.HTTP_201_CREATED,
    )


@admin_faqs_router.get("/{id}", summary="Get FAQ details for admin")
async def admin_get_faq(
    id: str,
    admin_user: User = Depends(require_admin),
):
    """Fetch complete FAQ details for editing."""
    faq = await get_faq_or_404(id)
    return success_response(
        data=serialize_faq(faq).model_dump(),
        message="اطلاعات سوال متداول دریافت شد",
    )


@admin_faqs_router.put("/{id}", summary="Update an existing FAQ item")
async def admin_update_faq(
    id: str,
    payload: FAQUpdateRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Update question, answer, order, or active status of an FAQ item."""
    faq = await get_faq_or_404(id)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="هیچ تغییری برای ذخیره‌سازی ارسال نشده است",
        )

    for field, val in update_data.items():
        if val is not None:
            if isinstance(val, str):
                val = val.strip()
            setattr(faq, field, val)

    faq.updated_at = datetime.utcnow()
    await faq.save()

    await AuditLogService.log_action(
        user=admin_user,
        action="UPDATE_FAQ",
        resource=f"faq_{faq.id}",
        details={"question": faq.question, "order": faq.order, "is_active": faq.is_active},
        request=request,
    )

    return success_response(
        data=serialize_faq(faq).model_dump(),
        message="سوال متداول با موفقیت بروزرسانی شد",
    )


@admin_faqs_router.patch("/{id}/toggle-active", summary="Toggle FAQ active status")
async def admin_toggle_faq_active(
    id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Toggle publish status between active and inactive."""
    faq = await get_faq_or_404(id)

    current_status = getattr(faq, "is_active", True)
    faq.is_active = not current_status
    faq.updated_at = datetime.utcnow()
    await faq.save()

    status_str = "فعال" if faq.is_active else "غیرفعال"
    await AuditLogService.log_action(
        user=admin_user,
        action="TOGGLE_FAQ_STATUS",
        resource=f"faq_{faq.id}",
        details={"is_active": faq.is_active},
        request=request,
    )

    return success_response(
        data=serialize_faq(faq).model_dump(),
        message=f"وضعیت سوال متداول به {status_str} تغییر کرد",
    )


@admin_faqs_router.patch("/reorder", summary="Batch reorder multiple FAQs")
async def admin_reorder_faqs(
    payload: FAQReorderRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Update display order for a list of FAQ IDs."""
    if not payload.items:
        return success_response(data=[], message="ترتیب سوالات متداول بروزرسانی شد")

    updated_faqs = []
    for item in payload.items:
        try:
            faq = await FAQ.get(PydanticObjectId(item.id))
            if faq:
                faq.order = item.order
                faq.updated_at = datetime.utcnow()
                await faq.save()
                updated_faqs.append(faq)
        except Exception:
            continue

    await AuditLogService.log_action(
        user=admin_user,
        action="REORDER_FAQS",
        resource="faqs",
        details={"updated_count": len(updated_faqs)},
        request=request,
    )

    items = [serialize_faq(f).model_dump() for f in updated_faqs]
    return success_response(
        data=items,
        message="ترتیب نمایش سوالات متداول با موفقیت بروزرسانی شد",
    )


@admin_faqs_router.delete("/{id}", summary="Delete an FAQ item")
async def admin_delete_faq(
    id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Permanently delete an FAQ item."""
    faq = await get_faq_or_404(id)
    faq_id = str(faq.id)
    question = faq.question

    await faq.delete()

    await AuditLogService.log_action(
        user=admin_user,
        action="DELETE_FAQ",
        resource=f"faq_{faq_id}",
        details={"question": question},
        request=request,
    )

    return success_response(
        data={"id": faq_id},
        message="سوال متداول با موفقیت حذف شد",
    )
