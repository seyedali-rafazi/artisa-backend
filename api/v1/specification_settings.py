"""Specification Settings Router — Admin Endpoints for Product Technical Specifications."""

from datetime import datetime
from typing import List, Optional
import re

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from dependencies.permissions import require_admin
from models.specification_setting import SpecificationSetting
from models.user import User
from schemas.specification_setting import (
    SpecificationSettingCreate,
    SpecificationSettingResponse,
    SpecificationSettingUpdate,
)
from schemas.response import error_response, success_response
from services.audit_service import AuditLogService

admin_specification_settings_router = APIRouter(
    prefix="/admin/specification-settings",
    tags=["Admin Specification Settings"],
)


def build_persian_regex(term: str) -> str:
    """Build a flexible regex pattern matching Persian and Arabic character variants safely."""
    char_map = {
        "ی": "[یي]",
        "ي": "[یي]",
        "ک": "[کك]",
        "ك": "[کك]",
        "آ": "[آاأإ]",
        "ا": "[آاأإ]",
        "أ": "[آاأإ]",
        "إ": "[آاأإ]",
        "ه": "[هة]",
        "ة": "[هة]",
        " ": r"[\s\u200c]+",
        "\u200c": r"[\s\u200c]+",
    }
    chars = []
    for c in term.strip():
        if c in char_map:
            chars.append(char_map[c])
        else:
            chars.append(re.escape(c))
    return "".join(chars)


def serialize_setting(s: SpecificationSetting) -> SpecificationSettingResponse:
    """Map SpecificationSetting document to response schema."""
    return SpecificationSettingResponse(
        id=str(s.id),
        title=s.title,
        default_value=s.default_value or "",
        category=s.category,
        description=s.description,
        order=s.order if s.order is not None else 0,
        is_active=s.is_active if s.is_active is not None else True,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


@admin_specification_settings_router.get(
    "",
    summary="List all product specification settings presets",
)
@admin_specification_settings_router.get("/", include_in_schema=False)
async def list_specification_settings(
    search: Optional[str] = Query(None, description="Search term for title or default value"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    active_only: bool = Query(False, description="Filter only active settings"),
    admin_user: User = Depends(require_admin),
):
    """Retrieve saved specification settings with search and filtering from database."""
    query = {}

    if active_only:
        query["is_active"] = True

    if category and category.strip() and category != "all" and category != "همه":
        query["$or"] = [
            {"category": category.strip()},
            {"category": "عمومی"},
            {"category": None},
            {"category": ""},
        ]

    if search and search.strip():
        term = search.strip()
        p_regex = build_persian_regex(term)
        regex_query = {"$regex": p_regex, "$options": "i"}
        search_filter = {
            "$or": [
                {"title": regex_query},
                {"default_value": regex_query},
                {"category": regex_query},
                {"description": regex_query},
            ]
        }
        if "$or" in query:
            query = {"$and": [query, search_filter]}
        else:
            query.update(search_filter)

    items = (
        await SpecificationSetting.find(query)
        .sort([("order", 1), ("created_at", 1)])
        .to_list()
    )

    data = [serialize_setting(item).model_dump() for item in items]
    return success_response(
        data=data,
        message="لیست تنظیمات مشخصات فنی دریافت شد",
    )


@admin_specification_settings_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new specification setting preset",
)
@admin_specification_settings_router.post("/", include_in_schema=False)
async def create_specification_setting(
    payload: SpecificationSettingCreate,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Create a new specification setting preset."""
    trimmed_title = payload.title.strip()
    if not trimmed_title:
        return error_response(
            message="عنوان مشخصه فنی نمی‌تواند خالی باشد",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Check for existing duplicate title
    existing = await SpecificationSetting.find_one(
        {"title": {"$regex": f"^{re.escape(trimmed_title)}$", "$options": "i"}}
    )
    if existing:
        # If existing exists, update default_value if provided and return it
        if payload.default_value and payload.default_value.strip():
            existing.default_value = payload.default_value.strip()
            existing.updated_at = datetime.utcnow()
            await existing.save()
        return success_response(
            data=serialize_setting(existing).model_dump(),
            message="مشخصه فنی قبلاً ثبت شده بود و اطلاعات آن بروزرسانی گردید",
            status_code=status.HTTP_200_OK,
        )

    setting = SpecificationSetting(
        title=trimmed_title,
        default_value=(payload.default_value or "").strip(),
        category=(payload.category or "").strip() or None,
        description=(payload.description or "").strip() or None,
        order=payload.order or 0,
        is_active=payload.is_active if payload.is_active is not None else True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await setting.insert()

    await AuditLogService.log_action(
        user=admin_user,
        action="create_specification_setting",
        resource=f"specification_setting/{setting.id}",
        details={"title": setting.title, "default_value": setting.default_value},
        request=request,
    )

    return success_response(
        data=serialize_setting(setting).model_dump(),
        message="مشخصه فنی جدید با موفقیت ایجاد گردید",
        status_code=status.HTTP_201_CREATED,
    )


@admin_specification_settings_router.put(
    "/{setting_id}",
    summary="Update an existing specification setting preset",
)
async def update_specification_setting(
    setting_id: str,
    payload: SpecificationSettingUpdate,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Update specification setting by ID."""
    try:
        setting = await SpecificationSetting.get(PydanticObjectId(setting_id))
    except Exception:
        setting = None

    if not setting:
        return error_response(
            message="تنظیمات مشخصه فنی مورد نظر یافت نشد",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    update_dict = payload.model_dump(exclude_unset=True)
    if "title" in update_dict and update_dict["title"]:
        setting.title = update_dict["title"].strip()
    if "default_value" in update_dict:
        setting.default_value = (update_dict["default_value"] or "").strip()
    if "category" in update_dict:
        setting.category = (update_dict["category"] or "").strip() or None
    if "description" in update_dict:
        setting.description = (update_dict["description"] or "").strip() or None
    if "order" in update_dict and update_dict["order"] is not None:
        setting.order = update_dict["order"]
    if "is_active" in update_dict and update_dict["is_active"] is not None:
        setting.is_active = update_dict["is_active"]

    setting.updated_at = datetime.utcnow()
    await setting.save()

    await AuditLogService.log_action(
        user=admin_user,
        action="update_specification_setting",
        resource=f"specification_setting/{setting.id}",
        details={"updated_fields": list(update_dict.keys())},
        request=request,
    )

    return success_response(
        data=serialize_setting(setting).model_dump(),
        message="مشخصه فنی با موفقیت بروزرسانی شد",
    )


@admin_specification_settings_router.delete(
    "/{setting_id}",
    summary="Delete a specification setting preset",
)
async def delete_specification_setting(
    setting_id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Delete specification setting by ID."""
    try:
        setting = await SpecificationSetting.get(PydanticObjectId(setting_id))
    except Exception:
        setting = None

    if not setting:
        return error_response(
            message="تنظیمات مشخصه فنی مورد نظر یافت نشد",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    title = setting.title
    await setting.delete()

    await AuditLogService.log_action(
        user=admin_user,
        action="delete_specification_setting",
        resource=f"specification_setting/{setting_id}",
        details={"title": title},
        request=request,
    )

    return success_response(
        message="مشخصه فنی با موفقیت حذف گردید",
    )
