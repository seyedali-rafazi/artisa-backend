"""Contact Messages Router — Public & Admin Endpoints."""

from datetime import datetime
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from dependencies.permissions import require_admin
from models.contact_message import ContactMessage
from models.user import User
from schemas.contact_message import (
    ContactMessageCreate,
    ContactMessageResponse,
    ContactMessageStatusUpdate,
    PaginatedContactMessagesResponse,
)
from schemas.response import success_response
from services.audit_service import AuditLogService

# Public router & admin router
router = APIRouter()
admin_contact_messages_router = APIRouter(prefix="/admin/contact-messages", tags=["Admin Contact Messages"])


def serialize_contact_message(msg: ContactMessage) -> ContactMessageResponse:
    """Map ContactMessage Beanie document to ContactMessageResponse schema."""
    return ContactMessageResponse(
        id=str(msg.id),
        name=msg.name,
        email=msg.email,
        message=msg.message,
        status=getattr(msg, "status", "unread") or "unread",
        created_at=getattr(msg, "created_at", None),
        updated_at=getattr(msg, "updated_at", None),
    )


async def get_contact_message_or_404(msg_id: str) -> ContactMessage:
    """Fetch ContactMessage by string ID or raise 404 HTTPException."""
    try:
        msg = await ContactMessage.get(PydanticObjectId(msg_id))
    except Exception:
        msg = None

    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="پیام تماس مورد نظر یافت نشد",
        )
    return msg


# ─── PUBLIC ENDPOINT ─────────────────────────────────────────────────────────


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new contact message",
)
@router.post(
    "/",
    include_in_schema=False,
    status_code=status.HTTP_201_CREATED,
)
async def submit_contact_message(payload: ContactMessageCreate):
    """Public endpoint to receive user contact form inquiries."""
    msg = ContactMessage(
        name=payload.name,
        email=payload.email,
        message=payload.message,
        status="unread",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await msg.insert()

    return success_response(
        data=serialize_contact_message(msg).model_dump(),
        message="پیام شما با موفقیت ارسال شد. کارشناسان ما به زودی با شما در ارتباط خواهند بود.",
        status_code=status.HTTP_201_CREATED,
    )


# ─── ADMIN ENDPOINTS (Mounted at /api/v1/contact-messages and /api/v1/admin/contact-messages) ─


async def admin_list_messages_impl(
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
):
    """Shared query logic for listing contact messages in admin panel."""
    query_filter = {}

    if search and search.strip():
        s = search.strip()
        query_filter["$or"] = [
            {"name": {"$regex": s, "$options": "i"}},
            {"email": {"$regex": s, "$options": "i"}},
            {"message": {"$regex": s, "$options": "i"}},
        ]

    if status_filter and status_filter.strip() in ["read", "unread"]:
        query_filter["status"] = status_filter.strip()

    skip = (page - 1) * limit
    query = ContactMessage.find(query_filter).sort("-created_at")

    total = await query.count()
    messages = await query.skip(skip).limit(limit).to_list()
    unread_count = await ContactMessage.find({"status": "unread"}).count()

    items = [serialize_contact_message(m).model_dump() for m in messages]
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    paginated_data = PaginatedContactMessagesResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        unread_count=unread_count,
    ).model_dump()

    return success_response(
        data=paginated_data,
        message="لیست پیام‌های تماس دریافت شد",
    )


async def admin_get_message_impl(id: str, mark_as_read: bool = True):
    """Shared retrieval logic with automatic mark-as-read capability."""
    msg = await get_contact_message_or_404(id)

    if mark_as_read and msg.status == "unread":
        msg.status = "read"
        msg.updated_at = datetime.utcnow()
        await msg.save()

    return success_response(
        data=serialize_contact_message(msg).model_dump(),
        message="اطلاعات پیام دریافت شد",
    )


async def admin_update_status_impl(
    id: str,
    payload: ContactMessageStatusUpdate,
    request: Request,
    admin_user: User,
):
    """Shared status update logic."""
    msg = await get_contact_message_or_404(id)
    prev_status = msg.status
    msg.status = payload.status
    msg.updated_at = datetime.utcnow()
    await msg.save()

    await AuditLogService.log_action(
        user=admin_user,
        action="UPDATE_CONTACT_MESSAGE_STATUS",
        resource=f"contact_message_{msg.id}",
        details={
            "previous_status": prev_status,
            "new_status": msg.status,
            "sender_email": msg.email,
        },
        request=request,
    )

    status_str = "خوانده‌شده" if msg.status == "read" else "خوانده‌نشده"
    return success_response(
        data=serialize_contact_message(msg).model_dump(),
        message=f"وضعیت پیام به «{status_str}» تغییر یافت",
    )


async def admin_delete_message_impl(id: str, request: Request, admin_user: User):
    """Shared delete logic."""
    msg = await get_contact_message_or_404(id)
    msg_id = str(msg.id)
    sender_email = msg.email

    await msg.delete()

    await AuditLogService.log_action(
        user=admin_user,
        action="DELETE_CONTACT_MESSAGE",
        resource=f"contact_message_{msg_id}",
        details={"sender_email": sender_email},
        request=request,
    )

    return success_response(
        data={"id": msg_id},
        message="پیام با موفقیت حذف شد",
    )


# ─── Endpoints on /api/v1/contact-messages ─────────────────────────────────────


@router.get("", summary="List contact messages (Admin)")
@router.get("/", include_in_schema=False)
async def list_contact_messages(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search in name, email, or message"),
    status: Optional[str] = Query(None, description="Filter by status: unread, read, or all"),
    admin_user: User = Depends(require_admin),
):
    """Retrieve paginated contact messages with optional search and status filter."""
    return await admin_list_messages_impl(
        page=page, limit=limit, search=search, status_filter=status
    )


@router.get("/{id}", summary="Get single contact message (Admin)")
async def get_contact_message(
    id: str,
    mark_as_read: bool = Query(True, description="Mark as read automatically"),
    admin_user: User = Depends(require_admin),
):
    """Retrieve full details of a contact message and optionally mark it as read."""
    return await admin_get_message_impl(id=id, mark_as_read=mark_as_read)


@router.patch("/{id}", summary="Update contact message status (Admin)")
async def update_contact_message_status(
    id: str,
    payload: ContactMessageStatusUpdate,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Update read / unread status of a contact message."""
    return await admin_update_status_impl(
        id=id, payload=payload, request=request, admin_user=admin_user
    )


@router.delete("/{id}", summary="Delete contact message (Admin)")
async def delete_contact_message(
    id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Permanently delete a contact message."""
    return await admin_delete_message_impl(id=id, request=request, admin_user=admin_user)


# ─── Endpoints on /api/v1/admin/contact-messages (Aliases) ─────────────────────


@admin_contact_messages_router.get("", summary="List contact messages (Admin alias)")
@admin_contact_messages_router.get("/", include_in_schema=False)
async def admin_alias_list(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    admin_user: User = Depends(require_admin),
):
    return await admin_list_messages_impl(
        page=page, limit=limit, search=search, status_filter=status
    )


@admin_contact_messages_router.get("/{id}", summary="Get single contact message (Admin alias)")
async def admin_alias_get(
    id: str,
    mark_as_read: bool = Query(True),
    admin_user: User = Depends(require_admin),
):
    return await admin_get_message_impl(id=id, mark_as_read=mark_as_read)


@admin_contact_messages_router.patch("/{id}", summary="Update status (Admin alias)")
async def admin_alias_update(
    id: str,
    payload: ContactMessageStatusUpdate,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    return await admin_update_status_impl(
        id=id, payload=payload, request=request, admin_user=admin_user
    )


@admin_contact_messages_router.delete("/{id}", summary="Delete message (Admin alias)")
async def admin_alias_delete(
    id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    return await admin_delete_message_impl(id=id, request=request, admin_user=admin_user)
