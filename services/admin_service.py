"""Admin Service handling analytics, users, products, orders, and admin management."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from beanie import PydanticObjectId
from fastapi import HTTPException, status, Request
from passlib.context import CryptContext

from models.user import User, RoleEnum
from models.product import Product
from models.order import Order
from models.comment import Comment
from models.audit_log import AuditLog
from schemas.admin import (
    DashboardStatsResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    UserAdminResponse,
    AdminCreateRequest,
)
from services.audit_service import AuditLogService

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AdminService:
    """Service for Admin Dashboard business logic."""

    @staticmethod
    async def get_dashboard_analytics() -> DashboardStatsResponse:
        """Compute key performance indicators and chart data."""
        orders = await Order.all().to_list()
        products = await Product.all().to_list()
        users = await User.all().to_list()

        now = datetime.utcnow()
        today_str = now.strftime("%Y/%m/%d")
        current_month_prefix = now.strftime("%Y/%m")

        total_revenue = 0.0
        today_revenue = 0.0
        monthly_revenue = 0.0

        total_orders = len(orders)
        pending_orders = 0
        completed_orders = 0
        cancelled_orders = 0

        # Monthly analytics map
        monthly_rev_map: Dict[str, float] = {}
        monthly_count_map: Dict[str, int] = {}
        category_map: Dict[str, int] = {}
        product_sales_map: Dict[str, Dict[str, Any]] = {}

        for order in orders:
            price = float(order.totalPrice or 0.0)
            order_status = (order.status or "").lower()

            if order_status not in ["cancelled", "refunded"]:
                total_revenue += price
                if order.date and order.date.startswith(today_str):
                    today_revenue += price
                if order.date and order.date.startswith(current_month_prefix):
                    monthly_revenue += price

            if order_status == "pending":
                pending_orders += 1
            elif order_status in ["completed", "delivered"]:
                completed_orders += 1
            elif order_status in ["cancelled", "refunded"]:
                cancelled_orders += 1

            month_key = order.date[:7] if order.date and len(order.date) >= 7 else "نامشخص"
            monthly_rev_map[month_key] = monthly_rev_map.get(month_key, 0.0) + (price if order_status not in ["cancelled", "refunded"] else 0)
            monthly_count_map[month_key] = monthly_count_map.get(month_key, 0) + 1

            for item in order.items:
                p_name = item.name
                if p_name not in product_sales_map:
                    product_sales_map[p_name] = {
                        "name": p_name,
                        "sales": 0,
                        "revenue": 0.0,
                        "image": item.image,
                    }
                product_sales_map[p_name]["sales"] += item.quantity
                product_sales_map[p_name]["revenue"] += float(item.price * item.quantity)

        total_customers = sum(1 for u in users if u.normalized_role == RoleEnum.USER.value)
        total_products = len(products)
        low_stock_products = sum(1 for p in products if 0 < getattr(p, "stock_quantity", 100) <= 5)
        out_of_stock_products = sum(1 for p in products if getattr(p, "stock_quantity", 100) <= 0)

        for p in products:
            cat = p.category or "بدون دسته‌بندی"
            category_map[cat] = category_map.get(cat, 0) + 1

        # Format monthly revenue chart
        sorted_months = sorted(monthly_rev_map.keys())[-6:]
        monthly_revenue_chart = [
            {"month": m, "revenue": monthly_rev_map[m]} for m in sorted_months
        ]
        monthly_orders_chart = [
            {"month": m, "orders": monthly_count_map.get(m, 0)} for m in sorted_months
        ]

        categories_distribution = [
            {"category": k, "count": v} for k, v in category_map.items()
        ]

        best_selling_products = sorted(
            product_sales_map.values(), key=lambda x: x["sales"], reverse=True
        )[:5]

        return DashboardStatsResponse(
            total_revenue=total_revenue,
            today_revenue=today_revenue,
            monthly_revenue=monthly_revenue,
            total_orders=total_orders,
            pending_orders=pending_orders,
            completed_orders=completed_orders,
            cancelled_orders=cancelled_orders,
            total_customers=total_customers,
            total_products=total_products,
            low_stock_products=low_stock_products,
            out_of_stock_products=out_of_stock_products,
            monthly_revenue_chart=monthly_revenue_chart,
            monthly_orders_chart=monthly_orders_chart,
            categories_distribution=categories_distribution,
            best_selling_products=best_selling_products,
        )

    # ─────────────────── USER MANAGEMENT ───────────────────

    @staticmethod
    async def list_users(
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Fetch paginated user list with order aggregates."""
        skip = (page - 1) * limit
        query = User.find_all()

        all_users = await query.to_list()
        all_orders = await Order.all().to_list()

        # Build order counts and total spent per user
        user_orders_map: Dict[str, int] = {}
        user_spent_map: Dict[str, float] = {}
        for o in all_orders:
            if o.userId:
                user_orders_map[o.userId] = user_orders_map.get(o.userId, 0) + 1
                if o.status not in ["cancelled", "refunded"]:
                    user_spent_map[o.userId] = user_spent_map.get(o.userId, 0.0) + float(o.totalPrice or 0)

        # Normalize role parameter if provided
        target_role = None
        if role:
            r_clean = role.lower().strip()
            if r_clean in ["superadmin", "super_admin", "مدیر ارشد"]:
                target_role = RoleEnum.SUPER_ADMIN.value
            elif r_clean in ["admin", "مدیر سیستم", "مدیر"]:
                target_role = RoleEnum.ADMIN.value
            elif r_clean in ["user", "customer", "مشتری"]:
                target_role = RoleEnum.USER.value
            else:
                target_role = r_clean

        filtered = []
        for u in all_users:
            if search:
                s = search.lower().strip()
                name_val = (u.name or "").lower()
                email_val = (u.email or "").lower()
                phone_val = u.phone or ""
                role_val = u.normalized_role.lower()
                if s not in name_val and s not in email_val and s not in phone_val and s not in role_val:
                    continue
            if target_role and u.normalized_role != target_role:
                continue
            if is_active is not None and u.is_active != is_active:
                continue
            filtered.append(u)

        total = len(filtered)
        paginated_users = filtered[skip : skip + limit]

        items = []
        for u in paginated_users:
            uid = str(u.id)
            items.append(
                UserAdminResponse(
                    id=uid,
                    name=u.name,
                    email=u.email,
                    phone=u.phone,
                    role=u.normalized_role,
                    is_active=u.is_active,
                    is_verified=u.is_verified or u.email_verified,
                    total_orders=user_orders_map.get(uid, 0),
                    total_spent=user_spent_map.get(uid, 0.0),
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                )
            )

        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        return {
            "items": [i.model_dump() for i in items],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    @staticmethod
    async def update_user_status(
        admin_user: User, user_id: str, is_active: bool, request: Request
    ) -> User:
        """Activate or deactivate user account."""
        target_user = await User.get(PydanticObjectId(user_id))
        if not target_user:
            raise HTTPException(status_code=404, detail="کاربر یافت نشد")

        target_user.is_active = is_active
        target_user.updated_at = datetime.utcnow()
        await target_user.save()

        await AuditLogService.log_action(
            user=admin_user,
            action="UPDATE_USER_STATUS",
            resource=f"user_{user_id}",
            details={"is_active": is_active, "target_email": target_user.email},
            request=request,
        )

        return target_user

    @staticmethod
    async def update_user_role(
        super_admin: User, user_id: str, new_role: str, request: Request
    ) -> User:
        """Update user role (SUPER_ADMIN only)."""
        target_user = await User.get(PydanticObjectId(user_id))
        if not target_user:
            raise HTTPException(status_code=404, detail="کاربر یافت نشد")

        if new_role not in [RoleEnum.USER.value, RoleEnum.ADMIN.value, RoleEnum.SUPER_ADMIN.value]:
            raise HTTPException(status_code=400, detail="نقش وارد شده نامعتبر است")

        old_role = target_user.normalized_role
        target_user.role = new_role
        target_user.is_superuser = (new_role == RoleEnum.SUPER_ADMIN.value)
        target_user.updated_at = datetime.utcnow()
        await target_user.save()

        await AuditLogService.log_action(
            user=super_admin,
            action="CHANGE_USER_ROLE",
            resource=f"user_{user_id}",
            details={"old_role": old_role, "new_role": new_role, "target_email": target_user.email},
            request=request,
        )

        return target_user

    # ─────────────────── PRODUCT MANAGEMENT ───────────────────

    @staticmethod
    async def list_products(
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        category: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch paginated products for admin table."""
        skip = (page - 1) * limit
        all_products = await Product.all().to_list()

        filtered = []
        for p in all_products:
            if search:
                s = search.lower()
                if s not in p.name.lower() and (not p.nameEn or s not in p.nameEn.lower()):
                    continue
            if category and p.category != category:
                continue
            if status_filter and getattr(p, "status", "published") != status_filter:
                continue
            filtered.append(p)

        total = len(filtered)
        paginated = filtered[skip : skip + limit]

        items = []
        for p in paginated:
            p_dict = p.model_dump()
            p_dict["id"] = str(p.id)
            items.append(p_dict)

        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    @staticmethod
    async def create_product(
        admin_user: User, payload: ProductCreateRequest, request: Request
    ) -> Product:
        """Create new product."""
        product = Product(
            name=payload.name,
            nameEn=payload.nameEn,
            price=payload.price,
            oldPrice=payload.oldPrice,
            image=payload.image,
            gallery=payload.gallery,
            category=payload.category,
            categoryEn=payload.categoryEn,
            rating=payload.rating,
            isSpecial=payload.isSpecial,
            isBestSeller=payload.isBestSeller,
            description=payload.description,
            descriptionEn=payload.descriptionEn,
            specifications=payload.specifications,
            stock_quantity=payload.stock_quantity,
            sku=payload.sku,
            status=payload.status,
        )
        await product.insert()

        await AuditLogService.log_action(
            user=admin_user,
            action="CREATE_PRODUCT",
            resource=f"product_{product.id}",
            details={"product_name": product.name, "price": product.price},
            request=request,
        )

        return product

    @staticmethod
    async def update_product(
        admin_user: User, product_id: str, payload: ProductUpdateRequest, request: Request
    ) -> Product:
        """Update existing product and clean up replaced Blob images."""
        from services.image_upload import cleanup_replaced_urls

        product = await Product.get(PydanticObjectId(product_id))
        if not product:
            raise HTTPException(status_code=404, detail="محصول یافت نشد")

        previous_urls = [product.image, *(product.gallery or [])]
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(product, key, value)

        product.updated_at = datetime.utcnow()
        await product.save()

        next_urls = [product.image, *(product.gallery or [])]
        await cleanup_replaced_urls(previous_urls=previous_urls, next_urls=next_urls)

        await AuditLogService.log_action(
            user=admin_user,
            action="UPDATE_PRODUCT",
            resource=f"product_{product_id}",
            details=update_data,
            request=request,
        )

        return product

    @staticmethod
    async def hard_delete_product(
        admin_user: User, product_id: str, request: Request
    ) -> None:
        """Permanently delete a product and its Blob images."""
        from services.blob_storage import delete_file

        product = await Product.get(PydanticObjectId(product_id))
        if not product:
            raise HTTPException(status_code=404, detail="محصول یافت نشد")

        from models.favorite import Favorite

        image_urls = [product.image, *(product.gallery or [])]
        await Favorite.find(Favorite.product_id == product_id).delete()
        await product.delete()
        await delete_file(image_urls)

        await AuditLogService.log_action(
            user=admin_user,
            action="DELETE_PRODUCT",
            resource=f"product_{product_id}",
            details={"name": product.name},
            request=request,
        )

    @staticmethod
    async def archive_product(
        admin_user: User, product_id: str, request: Request
    ) -> Product:
        """Archive (soft delete) a product."""
        product = await Product.get(PydanticObjectId(product_id))
        if not product:
            raise HTTPException(status_code=404, detail="محصول یافت نشد")

        product.status = "archived"
        product.updated_at = datetime.utcnow()
        await product.save()

        await AuditLogService.log_action(
            user=admin_user,
            action="ARCHIVE_PRODUCT",
            resource=f"product_{product_id}",
            details={"name": product.name},
            request=request,
        )

        return product

    @staticmethod
    async def restore_product(
        admin_user: User, product_id: str, request: Request
    ) -> Product:
        """Restore an archived product."""
        product = await Product.get(PydanticObjectId(product_id))
        if not product:
            raise HTTPException(status_code=404, detail="محصول یافت نشد")

        product.status = "published"
        product.updated_at = datetime.utcnow()
        await product.save()

        await AuditLogService.log_action(
            user=admin_user,
            action="RESTORE_PRODUCT",
            resource=f"product_{product_id}",
            details={"name": product.name},
            request=request,
        )

        return product

    @staticmethod
    async def duplicate_product(
        admin_user: User, product_id: str, request: Request
    ) -> Product:
        """Duplicate a product."""
        source = await Product.get(PydanticObjectId(product_id))
        if not source:
            raise HTTPException(status_code=404, detail="محصول اصلی یافت نشد")

        new_product = Product(
            name=f"{source.name} (رونوشت)",
            nameEn=f"{source.nameEn} (Copy)",
            price=source.price,
            oldPrice=source.oldPrice,
            image=source.image,
            gallery=source.gallery,
            category=source.category,
            categoryEn=source.categoryEn,
            rating=source.rating,
            isSpecial=source.isSpecial,
            isBestSeller=source.isBestSeller,
            description=source.description,
            descriptionEn=source.descriptionEn,
            specifications=source.specifications,
            stock_quantity=getattr(source, "stock_quantity", 100),
            sku=f"{source.sku}-COPY" if source.sku else None,
            status="draft",
        )
        await new_product.insert()

        await AuditLogService.log_action(
            user=admin_user,
            action="DUPLICATE_PRODUCT",
            resource=f"product_{new_product.id}",
            details={"source_id": product_id, "new_name": new_product.name},
            request=request,
        )

        return new_product

    # ─────────────────── ORDER MANAGEMENT ───────────────────

    @staticmethod
    async def list_orders(
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch paginated order list."""
        skip = (page - 1) * limit
        all_orders = await Order.all().to_list()

        filtered = []
        for o in all_orders:
            if search:
                s = search.lower()
                customer_name = o.shippingAddress.fullName if o.shippingAddress else ""
                if s not in o.orderId.lower() and s not in customer_name.lower():
                    continue
            if status_filter and o.status != status_filter:
                continue
            filtered.append(o)

        total = len(filtered)
        paginated = filtered[skip : skip + limit]

        items = []
        for o in paginated:
            o_dict = o.model_dump()
            o_dict["id"] = str(o.id)
            items.append(o_dict)

        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    @staticmethod
    async def update_order_status(
        admin_user: User,
        order_id: str,
        new_status: str,
        payment_status: Optional[str],
        request: Request,
    ) -> Order:
        """Update order status."""
        order = await Order.find_one(Order.orderId == order_id)
        if not order:
            try:
                order = await Order.get(PydanticObjectId(order_id))
            except Exception:
                order = None

        if not order:
            raise HTTPException(status_code=404, detail="سفارش یافت نشد")

        old_status = order.status
        order.status = new_status
        if payment_status:
            order.paymentStatus = payment_status

        order.updated_at = datetime.utcnow()
        await order.save()

        await AuditLogService.log_action(
            user=admin_user,
            action="UPDATE_ORDER_STATUS",
            resource=f"order_{order.orderId}",
            details={"old_status": old_status, "new_status": new_status, "payment_status": order.paymentStatus},
            request=request,
        )

        return order

    @staticmethod
    async def approve_order_payment(
        admin_user: User,
        order_id: str,
        request: Request,
    ) -> Order:
        """Approve card-to-card payment receipt, update order status to processing, and decrement product stock."""
        clean_id = order_id.strip()
        if not clean_id.startswith("ORD-") and clean_id.isdigit():
            clean_id = f"ORD-{clean_id}"

        order = await Order.find_one(Order.orderId == clean_id)
        if not order:
            try:
                order = await Order.get(PydanticObjectId(order_id))
            except Exception:
                order = None

        if not order:
            raise HTTPException(status_code=404, detail="سفارش یافت نشد")

        if order.paymentStatus == "payment_approved":
            raise HTTPException(
                status_code=400,
                detail="این پرداخت قبلاً تایید شده است و امکان تایید مجدد وجود ندارد.",
            )

        old_payment_status = order.paymentStatus
        order.paymentStatus = "payment_approved"
        order.status = "processing"
        order.approved_at = datetime.utcnow()
        order.updated_at = datetime.utcnow()
        await order.save()

        # Safely decrement stock quantity for each ordered item
        for item in order.items:
            try:
                p = await Product.get(PydanticObjectId(item.id))
            except Exception:
                p = None
            if not p:
                p = await Product.find_one(Product.id == item.id)

            if p:
                current_stock = getattr(p, "stock_quantity", 100)
                p.stock_quantity = max(0, current_stock - item.quantity)
                p.updated_at = datetime.utcnow()
                await p.save()

        await AuditLogService.log_action(
            user=admin_user,
            action="APPROVE_PAYMENT",
            resource=f"order_{order.orderId}",
            details={"old_payment_status": old_payment_status, "total_price": order.totalPrice},
            request=request,
        )

        return order

    @staticmethod
    async def reject_order_payment(
        admin_user: User,
        order_id: str,
        rejection_reason: Optional[str],
        request: Request,
    ) -> Order:
        """Reject card-to-card payment receipt with reason."""
        clean_id = order_id.strip()
        if not clean_id.startswith("ORD-") and clean_id.isdigit():
            clean_id = f"ORD-{clean_id}"

        order = await Order.find_one(Order.orderId == clean_id)
        if not order:
            try:
                order = await Order.get(PydanticObjectId(order_id))
            except Exception:
                order = None

        if not order:
            raise HTTPException(status_code=404, detail="سفارش یافت نشد")

        old_payment_status = order.paymentStatus
        order.paymentStatus = "payment_rejected"
        order.rejectionReason = rejection_reason or "فیش واریزی توسط مدیریت رد شد. لطفاً فیش معتبر جدید بارگذاری کنید."
        order.rejected_at = datetime.utcnow()
        order.updated_at = datetime.utcnow()
        await order.save()

        await AuditLogService.log_action(
            user=admin_user,
            action="REJECT_PAYMENT",
            resource=f"order_{order.orderId}",
            details={"old_payment_status": old_payment_status, "rejection_reason": order.rejectionReason},
            request=request,
        )

        return order

    # ─────────────────── ADMIN MANAGEMENT (SUPER_ADMIN ONLY) ───────────────────

    @staticmethod
    async def list_admins() -> List[Dict[str, Any]]:
        """List all admin and super admin accounts."""
        users = await User.all().to_list()
        admins = [u for u in users if u.is_admin_user]

        result = []
        for a in admins:
            result.append(
                {
                    "id": str(a.id),
                    "name": a.name,
                    "email": a.email,
                    "phone": a.phone,
                    "role": a.normalized_role,
                    "is_active": a.is_active,
                    "is_superuser": a.is_superuser,
                    "created_at": a.created_at,
                }
            )
        return result

    @staticmethod
    async def create_admin(
        super_admin: User, payload: AdminCreateRequest, request: Request
    ) -> User:
        """Create new Admin account (SUPER_ADMIN only)."""
        existing = await User.find_one(User.email == payload.email)
        if existing:
            raise HTTPException(status_code=400, detail="این آدرس ایمیل قبلاً ثبت شده است.")

        hashed_pwd = pwd_context.hash(payload.password)
        new_role = payload.role if payload.role in [RoleEnum.ADMIN.value, RoleEnum.SUPER_ADMIN.value] else RoleEnum.ADMIN.value

        admin_user = User(
            name=payload.name,
            email=payload.email,
            hashed_password=hashed_pwd,
            phone=payload.phone,
            role=new_role,
            is_superuser=(new_role == RoleEnum.SUPER_ADMIN.value),
            is_active=True,
            is_verified=True,
            email_verified=True,
            provider="local",
        )
        await admin_user.insert()

        await AuditLogService.log_action(
            user=super_admin,
            action="CREATE_ADMIN",
            resource=f"user_{admin_user.id}",
            details={"admin_email": admin_user.email, "role": new_role},
            request=request,
        )

        return admin_user

    @staticmethod
    async def delete_admin(
        super_admin: User, admin_id: str, request: Request
    ) -> bool:
        """Delete an admin account while enforcing last Super Admin protection."""
        target = await User.get(PydanticObjectId(admin_id))
        if not target:
            raise HTTPException(status_code=404, detail="حساب مدیر یافت نشد")

        if target.id == super_admin.id:
            raise HTTPException(status_code=400, detail="شما نمی‌توانید حساب خودتان را حذف کنید")

        if target.is_super_admin_user:
            all_users = await User.all().to_list()
            super_admin_count = sum(1 for u in all_users if u.is_super_admin_user and u.is_active)
            if super_admin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="امکان حذف آخرین مدیر ارشد (Super Admin) وجود ندارد.",
                )

        target_email = target.email
        await target.delete()

        await AuditLogService.log_action(
            user=super_admin,
            action="DELETE_ADMIN",
            resource=f"user_{admin_id}",
            details={"deleted_email": target_email},
            request=request,
        )

        return True

    # ─────────────────── AUDIT LOGS ───────────────────

    @staticmethod
    async def list_audit_logs(
        page: int = 1, limit: int = 20, search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch audit logs (SUPER_ADMIN only)."""
        skip = (page - 1) * limit
        all_logs = await AuditLog.find_all().sort("-created_at").to_list()

        filtered = []
        for log in all_logs:
            if search:
                s = search.lower()
                if (
                    s not in log.user_email.lower()
                    and s not in log.action.lower()
                    and s not in log.resource.lower()
                ):
                    continue
            filtered.append(log)

        total = len(filtered)
        paginated = filtered[skip : skip + limit]

        items = []
        for l in paginated:
            l_dict = l.model_dump()
            l_dict["id"] = str(l.id)
            items.append(l_dict)

        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    # ─────────────────── COMMENT MANAGEMENT ───────────────────

    @staticmethod
    async def list_comments(
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        product_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch paginated comments for administration."""
        skip = (page - 1) * limit
        query = Comment.find(Comment.is_deleted == False).sort("-created_at")

        all_comments = await query.to_list()
        all_products = await Product.all().to_list()
        product_map = {str(p.id): p.name for p in all_products}

        filtered = []
        for c in all_comments:
            if product_id and c.productId != product_id:
                continue
            if status_filter and c.status != status_filter:
                continue
            if type_filter:
                c_type = getattr(c, "type", "comment") or "comment"
                if type_filter == "comment" and c_type != "comment":
                    continue
                if type_filter == "question" and c_type != "question":
                    continue
            if search:
                s = search.lower()
                p_name = product_map.get(c.productId, "").lower()
                user_name = (c.userName or "").lower()
                text_val = (c.text or "").lower()
                if s not in p_name and s not in user_name and s not in text_val:
                    continue
            filtered.append(c)

        total = len(filtered)
        paginated = filtered[skip : skip + limit]

        items = []
        for c in paginated:
            items.append({
                "id": str(c.id),
                "productId": c.productId,
                "productName": product_map.get(c.productId, "محصول آرتیسا"),
                "userId": c.userId,
                "userName": c.userName,
                "userEmail": c.userEmail,
                "text": c.text,
                "rating": c.rating,
                "type": getattr(c, "type", "comment") or "comment",
                "reply": getattr(c, "reply", None),
                "replyDate": getattr(c, "replyDate", None),
                "status": c.status,
                "date": c.date,
                "created_at": c.created_at,
                "moderated_by": c.moderated_by,
                "moderated_at": c.moderated_at,
            })

        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    @staticmethod
    async def update_comment_status(
        admin_user: User,
        comment_id: str,
        status_val: Optional[str] = None,
        text: Optional[str] = None,
        rating: Optional[int] = None,
        type_val: Optional[str] = None,
        reply: Optional[str] = None,
        request: Request = None,
    ) -> Comment:
        """Moderate status, add reply, or edit comment as Admin."""
        try:
            comment = await Comment.get(PydanticObjectId(comment_id))
        except Exception:
            comment = None

        if not comment or comment.is_deleted:
            raise HTTPException(status_code=404, detail="نظر مورد نظر یافت نشد")

        old_status = comment.status
        if status_val:
            comment.status = status_val
        if text:
            comment.text = text
        if rating:
            comment.rating = rating
        if type_val:
            comment.type = type_val

        if reply is not None:
            comment.reply = reply
            comment.replyDate = datetime.now().strftime("%Y/%m/%d")
            comment.status = "approved"

        comment.moderated_by = admin_user.name
        comment.moderated_at = datetime.utcnow()
        comment.updated_at = datetime.utcnow()
        await comment.save()

        if request:
            await AuditLogService.log_action(
                user=admin_user,
                action="UPDATE_COMMENT_STATUS",
                resource=f"comment_{comment_id}",
                details={"old_status": old_status, "new_status": comment.status, "product_id": comment.productId, "reply": reply},
                request=request,
            )

        return comment

    @staticmethod
    async def delete_comment(
        admin_user: User, comment_id: str, request: Request
    ) -> bool:
        """Soft delete a comment as Admin."""
        try:
            comment = await Comment.get(PydanticObjectId(comment_id))
        except Exception:
            comment = None

        if not comment or comment.is_deleted:
            raise HTTPException(status_code=404, detail="نظر مورد نظر یافت نشد")

        comment.is_deleted = True
        comment.updated_at = datetime.utcnow()
        await comment.save()

        await AuditLogService.log_action(
            user=admin_user,
            action="DELETE_COMMENT",
            resource=f"comment_{comment_id}",
            details={"product_id": comment.productId, "author": comment.userName},
            request=request,
        )

        return True

