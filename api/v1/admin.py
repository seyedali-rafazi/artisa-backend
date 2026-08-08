"""Admin API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException, status, Request
from models.user import User
from dependencies.permissions import require_admin, require_super_admin
from services.admin_service import AdminService
from services.image_upload import process_and_upload_image
from schemas.admin import (
    DashboardStatsResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    UserStatusUpdateRequest,
    UserRoleUpdateRequest,
    OrderStatusUpdateRequest,
    AdminCreateRequest,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ─── 1. DASHBOARD & ANALYTICS ───────────────────────────────────────────────


@router.get("/analytics/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_analytics(admin_user: User = Depends(require_admin)):
    """Get dashboard analytics, revenue charts, and KPIs."""
    return await AdminService.get_dashboard_analytics()


# ─── 2. USER MANAGEMENT ─────────────────────────────────────────────────────


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin_user: User = Depends(require_admin),
):
    """List paginated users with order statistics."""
    return await AdminService.list_users(
        page=page, limit=limit, search=search, role=role, is_active=is_active
    )


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    payload: UserStatusUpdateRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Activate or deactivate user account."""
    updated = await AdminService.update_user_status(
        admin_user=admin_user, user_id=user_id, is_active=payload.is_active, request=request
    )
    return {"message": "وضعیت کاربر با موفقیت تغییر کرد", "is_active": updated.is_active}


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    payload: UserRoleUpdateRequest,
    request: Request,
    super_admin: User = Depends(require_super_admin),
):
    """Assign user role (SUPER_ADMIN only)."""
    updated = await AdminService.update_user_role(
        super_admin=super_admin, user_id=user_id, new_role=payload.role, request=request
    )
    return {"message": "نقش کاربر با موفقیت بروزرسانی شد", "role": updated.normalized_role}


# ─── 3. PRODUCT MANAGEMENT ─────────────────────────────────────────────────


@router.get("/products")
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    admin_user: User = Depends(require_admin),
):
    """List paginated products for administration."""
    return await AdminService.list_products(
        page=page, limit=limit, search=search, category=category, status_filter=status_filter
    )


@router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreateRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Create new product."""
    product = await AdminService.create_product(
        admin_user=admin_user, payload=payload, request=request
    )
    res = product.model_dump()
    res["id"] = str(product.id)
    return res


@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    payload: ProductUpdateRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Update existing product."""
    product = await AdminService.update_product(
        admin_user=admin_user, product_id=product_id, payload=payload, request=request
    )
    res = product.model_dump()
    res["id"] = str(product.id)
    return res


@router.delete("/products/{product_id}")
async def archive_product(
    product_id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Archive (soft delete) a product."""
    product = await AdminService.archive_product(
        admin_user=admin_user, product_id=product_id, request=request
    )
    return {"message": "محصول با موفقیت آرشیو شد", "status": product.status}


@router.delete("/products/{product_id}/permanent")
async def delete_product_permanently(
    product_id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Permanently delete a product and its Blob images."""
    await AdminService.hard_delete_product(
        admin_user=admin_user, product_id=product_id, request=request
    )
    return {"message": "محصول با موفقیت و به صورت دائمی حذف شد"}


@router.post("/products/{product_id}/restore")
async def restore_product(
    product_id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Restore an archived product."""
    product = await AdminService.restore_product(
        admin_user=admin_user, product_id=product_id, request=request
    )
    return {"message": "محصول با موفقیت بازیابی شد", "status": product.status}


@router.post("/products/{product_id}/duplicate")
async def duplicate_product(
    product_id: str,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Duplicate a product."""
    new_product = await AdminService.duplicate_product(
        admin_user=admin_user, product_id=product_id, request=request
    )
    res = new_product.model_dump()
    res["id"] = str(new_product.id)
    return res


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    admin_user: User = Depends(require_admin),
):
    """Upload product image or gallery asset to Vercel Blob."""
    uploaded = await process_and_upload_image(file)
    return {
        "url": uploaded.url,
        "pathname": uploaded.pathname,
        "filename": uploaded.filename,
        "content_type": uploaded.content_type,
    }


# ─── 4. ORDER MANAGEMENT ───────────────────────────────────────────────────


@router.get("/orders")
async def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    admin_user: User = Depends(require_admin),
):
    """List paginated orders."""
    return await AdminService.list_orders(
        page=page, limit=limit, search=search, status_filter=status_filter
    )


@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    payload: OrderStatusUpdateRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
):
    """Update order and payment status."""
    order = await AdminService.update_order_status(
        admin_user=admin_user,
        order_id=order_id,
        new_status=payload.status,
        payment_status=payload.paymentStatus,
        request=request,
    )
    return {"message": "وضعیت سفارش بروزرسانی شد", "status": order.status}


# ─── 5. ADMIN MANAGEMENT (SUPER_ADMIN ONLY) ─────────────────────────────────


@router.get("/admins")
async def list_admins(super_admin: User = Depends(require_super_admin)):
    """List all admin accounts (SUPER_ADMIN only)."""
    return await AdminService.list_admins()


@router.post("/admins", status_code=status.HTTP_201_CREATED)
async def create_admin(
    payload: AdminCreateRequest,
    request: Request,
    super_admin: User = Depends(require_super_admin),
):
    """Create a new Admin account (SUPER_ADMIN only)."""
    admin_user = await AdminService.create_admin(
        super_admin=super_admin, payload=payload, request=request
    )
    return {
        "id": str(admin_user.id),
        "name": admin_user.name,
        "email": admin_user.email,
        "role": admin_user.normalized_role,
    }


@router.delete("/admins/{admin_id}")
async def delete_admin(
    admin_id: str,
    request: Request,
    super_admin: User = Depends(require_super_admin),
):
    """Delete an Admin account (SUPER_ADMIN only)."""
    await AdminService.delete_admin(
        super_admin=super_admin, admin_id=admin_id, request=request
    )
    return {"message": "حساب مدیر با موفقیت حذف شد"}


# ─── 6. AUDIT LOGS (SUPER_ADMIN ONLY) ───────────────────────────────────────


@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    super_admin: User = Depends(require_super_admin),
):
    """List audit trail logs (SUPER_ADMIN only)."""
    return await AdminService.list_audit_logs(page=page, limit=limit, search=search)
