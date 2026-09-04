"""Banners Router — Public & Admin Endpoints."""

from datetime import datetime
from typing import List, Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from dependencies.permissions import require_admin
from models.banner import Banner, BannerTextElement, BannerPosition
from models.user import User
from schemas.banner import (
    BannerCreateRequest,
    BannerPositionSchema,
    BannerReorderRequest,
    BannerResponse,
    BannerStatusUpdateRequest,
    BannerTextElementSchema,
    BannerUpdateRequest,
)
from schemas.response import error_response, success_response
from services.audit_service import AuditLogService
from services.blob_storage import delete_file
from services.image_upload import cleanup_replaced_urls

router = APIRouter()
admin_banners_router = APIRouter(prefix="/admin/banners", tags=["Admin Banners"])


def serialize_banner(b: Banner) -> BannerResponse:
    """Map Banner document to BannerResponse schema safely handling legacy and modern records."""
    texts_data: List[BannerTextElementSchema] = []
    if getattr(b, "texts", None):
        for t in b.texts:
            pos = getattr(t, "position", None)
            pos_schema = (
                BannerPositionSchema(x=getattr(pos, "x", 50.0), y=getattr(pos, "y", 50.0))
                if pos
                else BannerPositionSchema(x=50.0, y=50.0)
            )
            texts_data.append(
                BannerTextElementSchema(
                    id=getattr(t, "id", ""),
                    text=getattr(t, "text", ""),
                    fontFamily=getattr(t, "fontFamily", "inherit") or "inherit",
                    fontSize=getattr(t, "fontSize", 24) or 24,
                    fontWeight=str(getattr(t, "fontWeight", "normal") or "normal"),
                    color=getattr(t, "color", "#FFFFFF") or "#FFFFFF",
                    textAlign=getattr(t, "textAlign", "center") or "center",
                    lineHeight=getattr(t, "lineHeight", 1.4),
                    letterSpacing=getattr(t, "letterSpacing", 0.0),
                    textShadow=getattr(t, "textShadow", None),
                    position=pos_schema,
                )
            )

    raw_is_active = getattr(b, "isActive", None)
    is_active = True if raw_is_active is None else bool(raw_is_active)

    return BannerResponse(
        id=str(b.id),
        title=getattr(b, "title", "") or "",
        image=getattr(b, "image", "") or "",
        texts=texts_data,
        link=getattr(b, "link", "") or "",
        linkOpenInNewTab=bool(getattr(b, "linkOpenInNewTab", False)),
        isActive=is_active,
        order=int(getattr(b, "order", 0) or 0),
        created_at=getattr(b, "created_at", None),
        updated_at=getattr(b, "updated_at", None),
        subtitle=getattr(b, "subtitle", "") or "",
        badge=getattr(b, "badge", "") or "",
        buttonText=getattr(b, "buttonText", "") or "",
    )


async def get_banner_or_404(banner_id: str) -> Banner:
    """Fetch Banner by ID or raise 404 HTTPException."""
    banner = None
    try:
        banner = await Banner.get(PydanticObjectId(banner_id))
    except Exception:
        banner = None

    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="بنر مورد نظر یافت نشد",
        )
    return banner


# ─── PUBLIC ENDPOINTS ─────────────────────────────────────────────────────────


@router.get("", summary="Get active hero slider banners for storefront")
@router.get("/", include_in_schema=False)
@router.get("/active", summary="Get active hero slider banners (alias)")
async def list_active_banners():
    """Retrieve list of active banners sorted by display order."""
    query_filter = {
        "$or": [
            {"isActive": True},
            {"isActive": {"$exists": False}},  # Support legacy documents without isActive
        ]
    }
    banners = await Banner.find(query_filter).sort("+order", "+_id").to_list()

    items = [serialize_banner(b).model_dump() for b in banners]
    return success_response(data=items, message="بنرهای صفحه اصلی دریافت شد")


@router.get("/{banner_id}", summary="Get single active banner item")
async def get_public_banner(banner_id: str):
    """Retrieve single public banner by ID."""
    banner = await get_banner_or_404(banner_id)
    if getattr(banner, "isActive", True) is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="بنر مورد نظر یافت نشد یا غیرفعال است",
        )
    return success_response(
        data=serialize_banner(banner).model_dump(),
        message="اطلاعات بنر دریافت شد",
    )


# ─── ADMIN ENDPOINTS ──────────────────────────────────────────────────────────


@admin_banners_router.get("", summary="List all banners for admin management")
@admin_banners_router.get("/", include_in_schema=False)
async def admin_list_banners(
    search: Optional[str] = Query(None, description="Search in title"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: active, inactive"),
    admin_user: User = Depends(require_admin),
):
    """Retrieve all banners (active and inactive) sorted by display order."""
    query_filter = {}
    if search and search.strip():
        query_filter["title"] = {"$regex": search.strip(), "$options": "i"}

    if status_filter == "active":
        query_filter["$or"] = [{"isActive": True}, {"isActive": {"$exists": False}}]
    elif status_filter == "inactive":
        query_filter["isActive"] = False

    banners = await Banner.find(query_filter).sort("+order", "+_id").to_list()
    items = [serialize_banner(b).model_dump() for b in banners]

    return success_response(
        data=items,
        message="لیست مدیریت بنرها با موفقیت دریافت شد",
    )


@admin_banners_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new banner",
)
@admin_banners_router.post("/", include_in_schema=False, status_code=status.HTTP_201_CREATED)
async def admin_create_banner(
    payload: BannerCreateRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Create a new banner with image Blob URL, typography texts, and positioning."""
    order_val = payload.order
    if order_val is None or order_val == 0:
        count = await Banner.count()
        order_val = count + 1

    # Map texts
    texts: List[BannerTextElement] = []
    for t in payload.texts:
        pos = BannerPosition(x=t.position.x, y=t.position.y)
        texts.append(
            BannerTextElement(
                id=t.id,
                text=t.text,
                fontFamily=t.fontFamily,
                fontSize=t.fontSize,
                fontWeight=t.fontWeight,
                color=t.color,
                textAlign=t.textAlign,
                lineHeight=t.lineHeight,
                letterSpacing=t.letterSpacing,
                textShadow=t.textShadow,
                position=pos,
            )
        )

    banner = Banner(
        title=payload.title.strip(),
        image=payload.image.strip(),
        texts=texts,
        link=(payload.link or "").strip(),
        linkOpenInNewTab=bool(payload.linkOpenInNewTab),
        isActive=payload.isActive if payload.isActive is not None else True,
        order=order_val,
        subtitle=payload.subtitle or "",
        badge=payload.badge or "",
        buttonText=payload.buttonText or "",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await banner.insert()

    await AuditLogService.log_action(
        user=admin_user,
        action="CREATE_BANNER",
        resource=f"banner_{banner.id}",
        details={"title": banner.title, "order": banner.order, "textsCount": len(banner.texts)},
        request=request,
    )

    return success_response(
        data=serialize_banner(banner).model_dump(),
        message="بنر جدید با موفقیت ایجاد شد",
        status_code=status.HTTP_201_CREATED,
    )


@admin_banners_router.get("/{banner_id}", summary="Get banner details for admin editing")
async def admin_get_banner(
    banner_id: str,
    admin_user: User = Depends(require_admin),
):
    """Fetch complete banner details for editing."""
    banner = await get_banner_or_404(banner_id)
    return success_response(
        data=serialize_banner(banner).model_dump(),
        message="اطلاعات بنر دریافت شد",
    )


@admin_banners_router.put("/{banner_id}", summary="Update an existing banner")
async def admin_update_banner(
    banner_id: str,
    payload: BannerUpdateRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Update banner details and clean up old Vercel Blob file if replaced."""
    banner = await get_banner_or_404(banner_id)
    previous_urls = [banner.image] if getattr(banner, "image", None) else []

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="هیچ تغییری برای ذخیره‌سازی ارسال نشده است",
        )

    if "title" in update_data and update_data["title"] is not None:
        banner.title = update_data["title"].strip()
    if "image" in update_data and update_data["image"] is not None:
        banner.image = update_data["image"].strip()
    if "link" in update_data and update_data["link"] is not None:
        banner.link = update_data["link"].strip()
    if "linkOpenInNewTab" in update_data and update_data["linkOpenInNewTab"] is not None:
        banner.linkOpenInNewTab = bool(update_data["linkOpenInNewTab"])
    if "isActive" in update_data and update_data["isActive"] is not None:
        banner.isActive = bool(update_data["isActive"])
    if "order" in update_data and update_data["order"] is not None:
        banner.order = int(update_data["order"])
    if "subtitle" in update_data and update_data["subtitle"] is not None:
        banner.subtitle = update_data["subtitle"]
    if "badge" in update_data and update_data["badge"] is not None:
        banner.badge = update_data["badge"]
    if "buttonText" in update_data and update_data["buttonText"] is not None:
        banner.buttonText = update_data["buttonText"]

    if "texts" in update_data and update_data["texts"] is not None:
        new_texts: List[BannerTextElement] = []
        for t in update_data["texts"]:
            pos_dict = t.get("position", {}) if isinstance(t, dict) else getattr(t, "position", {})
            if hasattr(pos_dict, "x"):
                pos_x = pos_dict.x
                pos_y = pos_dict.y
            else:
                pos_x = pos_dict.get("x", 50.0)
                pos_y = pos_dict.get("y", 50.0)

            t_id = t.get("id") if isinstance(t, dict) else getattr(t, "id", None)
            t_text = t.get("text") if isinstance(t, dict) else getattr(t, "text", "")
            t_font = t.get("fontFamily") if isinstance(t, dict) else getattr(t, "fontFamily", "inherit")
            t_size = t.get("fontSize") if isinstance(t, dict) else getattr(t, "fontSize", 24)
            t_weight = t.get("fontWeight") if isinstance(t, dict) else getattr(t, "fontWeight", "normal")
            t_color = t.get("color") if isinstance(t, dict) else getattr(t, "color", "#FFFFFF")
            t_align = t.get("textAlign") if isinstance(t, dict) else getattr(t, "textAlign", "center")
            t_line_height = t.get("lineHeight") if isinstance(t, dict) else getattr(t, "lineHeight", 1.4)
            t_spacing = t.get("letterSpacing") if isinstance(t, dict) else getattr(t, "letterSpacing", 0.0)
            t_shadow = t.get("textShadow") if isinstance(t, dict) else getattr(t, "textShadow", None)

            new_texts.append(
                BannerTextElement(
                    id=t_id or str(uuid.uuid4()),
                    text=t_text,
                    fontFamily=t_font or "inherit",
                    fontSize=t_size or 24,
                    fontWeight=str(t_weight or "normal"),
                    color=t_color or "#FFFFFF",
                    textAlign=t_align or "center",
                    lineHeight=t_line_height,
                    letterSpacing=t_spacing,
                    textShadow=t_shadow,
                    position=BannerPosition(x=pos_x, y=pos_y),
                )
            )
        banner.texts = new_texts

    banner.updated_at = datetime.utcnow()
    await banner.save()

    # Clean up old Blob image if image URL changed
    next_urls = [banner.image] if getattr(banner, "image", None) else []
    await cleanup_replaced_urls(previous_urls=previous_urls, next_urls=next_urls)

    await AuditLogService.log_action(
        user=admin_user,
        action="UPDATE_BANNER",
        resource=f"banner_{banner.id}",
        details={"title": banner.title, "order": banner.order, "isActive": banner.isActive},
        request=request,
    )

    return success_response(
        data=serialize_banner(banner).model_dump(),
        message="بنر با موفقیت بروزرسانی شد",
    )


@admin_banners_router.delete("/{banner_id}", summary="Delete a banner and its Vercel Blob image")
async def admin_delete_banner(
    banner_id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Delete a banner document and clean up its Vercel Blob asset."""
    banner = await get_banner_or_404(banner_id)
    image_urls = [banner.image] if getattr(banner, "image", None) else []

    await banner.delete()
    await delete_file(image_urls)

    await AuditLogService.log_action(
        user=admin_user,
        action="DELETE_BANNER",
        resource=f"banner_{banner.id}",
        details={"title": banner.title},
        request=request,
    )

    return success_response(message="بنر با موفقیت حذف شد")


@admin_banners_router.patch("/{banner_id}/status", summary="Toggle or update banner active status")
async def admin_update_banner_status(
    banner_id: str,
    payload: Optional[BannerStatusUpdateRequest] = None,
    request: Request = None,
    admin_user: User = Depends(require_admin),
):
    """Update active status of a banner."""
    banner = await get_banner_or_404(banner_id)

    if payload is not None:
        banner.isActive = payload.isActive
    else:
        banner.isActive = not getattr(banner, "isActive", True)

    banner.updated_at = datetime.utcnow()
    await banner.save()

    status_str = "فعال" if banner.isActive else "غیرفعال"
    if request:
        await AuditLogService.log_action(
            user=admin_user,
            action="UPDATE_BANNER_STATUS",
            resource=f"banner_{banner.id}",
            details={"isActive": banner.isActive},
            request=request,
        )

    return success_response(
        data=serialize_banner(banner).model_dump(),
        message=f"وضعیت بنر به {status_str} تغییر کرد",
    )


@admin_banners_router.patch("/order", summary="Batch reorder multiple banners")
@admin_banners_router.patch("/reorder", include_in_schema=False)
async def admin_reorder_banners(
    payload: BannerReorderRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Update display order for a list of banner IDs."""
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لیست تغییر ترتیب بنرها خالی است",
        )

    updated_ids = []
    for item in payload.items:
        try:
            banner = await Banner.get(PydanticObjectId(item.id))
            if banner:
                banner.order = item.order
                banner.updated_at = datetime.utcnow()
                await banner.save()
                updated_ids.append(item.id)
        except Exception:
            continue

    await AuditLogService.log_action(
        user=admin_user,
        action="REORDER_BANNERS",
        resource="banners_reorder",
        details={"updated_count": len(updated_ids)},
        request=request,
    )

    banners = await Banner.find_all().sort("+order", "+_id").to_list()
    items = [serialize_banner(b).model_dump() for b in banners]

    return success_response(
        data=items,
        message=f"ترتیب {len(updated_ids)} بنر با موفقیت بروزرسانی شد",
    )

