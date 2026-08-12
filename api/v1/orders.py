"""Orders Router."""

import random
from datetime import datetime
from typing import Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, UploadFile, status, HTTPException

from core.security import get_current_user, get_optional_user
from models.order import Order, OrderItem, ShippingAddress
from models.product import Product
from models.user import User
from schemas.order import OrderCreate, OrderResponse, OrderTrackingResponse, TrackingStep
from schemas.response import success_response, error_response
from services.image_upload import process_and_upload_image

router = APIRouter()


@router.post("", summary="Create order (Checkout)")
@router.post("/", include_in_schema=False)
async def create_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_user),
):
    """Place a new order upon checkout (authentication required)."""
    if not payload.items or len(payload.items) == 0:
        return error_response(
            message="سبد خرید خالی است", status_code=status.HTTP_400_BAD_REQUEST
        )

    # Server-side validation of cart items against DB
    items_models = []
    total_price = 0.0

    for item_input in payload.items:
        # Fetch product from DB by ID
        db_product = None
        try:
            db_product = await Product.get(PydanticObjectId(item_input.id))
        except Exception:
            db_product = None

        if not db_product:
            db_product = await Product.find_one(Product.id == item_input.id)

        if not db_product:
            return error_response(
                message=f"محصولی با شناسه {item_input.id} یافت نشد",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if getattr(db_product, "status", "published") != "published":
            return error_response(
                message=f"محصول «{db_product.name}» در حال حاضر قابل سفارش نیست",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        current_stock = getattr(db_product, "stock_quantity", 100)
        if current_stock < item_input.quantity:
            return error_response(
                message=f"موجودی محصول «{db_product.name}» کافی نیست (موجودی فعلی: {current_stock})",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        item_price = db_product.price
        item_total = item_price * item_input.quantity
        total_price += item_total

        items_models.append(
            OrderItem(
                id=str(db_product.id),
                name=db_product.name,
                price=item_price,
                quantity=item_input.quantity,
                image=db_product.image,
            )
        )

    # Generate 6-digit numeric order code
    numeric_code = str(random.randint(100000, 999999))
    order_id = f"ORD-{numeric_code}"

    shipping_info = ShippingAddress(
        fullName=payload.fullName,
        phone=payload.phone,
        postalCode=payload.postalCode,
        address=payload.address,
    )

    order = Order(
        orderId=order_id,
        userId=str(current_user.id),
        date=datetime.now().strftime("%Y/%m/%d"),
        status="pending",
        totalPrice=total_price,
        paymentStatus="pending_payment",
        paymentMethod="card",
        items=items_models,
        shippingAddress=shipping_info,
    )
    await order.insert()

    data = OrderResponse(
        id=order.orderId,
        date=order.date,
        status=order.status,
        totalPrice=order.totalPrice,
        paymentStatus=order.paymentStatus,
        paymentMethod=order.paymentMethod,
        receiptUrl=order.receiptUrl,
        rejectionReason=order.rejectionReason,
        items=[item.model_dump() for item in items_models],
        shippingAddress=shipping_info.model_dump(),
    ).model_dump()

    return success_response(
        data=data,
        message="سفارش با موفقیت ثبت شد. لطفاً فیش واریز کارت به کارت را بارگذاری کنید.",
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/{order_id}/receipt", summary="Upload card-to-card payment receipt")
async def upload_payment_receipt(
    order_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload payment receipt photo for an order."""
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
        return error_response(
            message="سفارش مورد نظر یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    # Authorization check: only order owner or admin
    if order.userId != str(current_user.id) and not current_user.is_admin_user:
        return error_response(
            message="شما دسترسی به این سفارش ندارید",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Process and upload image (validates file magic bytes and size <= 5MB)
    try:
        uploaded = await process_and_upload_image(file, folder="receipts")
    except HTTPException as exc:
        return error_response(
            message=exc.detail if isinstance(exc.detail, str) else "خطا در آپلود فیش پرداخت",
            status_code=exc.status_code,
        )

    # Update order receipt URL and transition payment status to review
    order.receiptUrl = uploaded.url
    order.paymentStatus = "payment_pending_review"
    order.updated_at = datetime.utcnow()
    await order.save()

    data = OrderResponse(
        id=order.orderId,
        date=order.date,
        status=order.status,
        totalPrice=order.totalPrice,
        paymentStatus=order.paymentStatus,
        paymentMethod=order.paymentMethod,
        receiptUrl=order.receiptUrl,
        rejectionReason=order.rejectionReason,
        items=[item.model_dump() for item in order.items],
        shippingAddress=order.shippingAddress.model_dump() if order.shippingAddress else None,
    ).model_dump()

    return success_response(
        data=data,
        message="تصویر فیش پرداخت با موفقیت بارگذاری شد و در انتظار بررسی مدیریت قرار گرفت",
    )


@router.get("", summary="Get current user order history")
@router.get("/", include_in_schema=False)
async def list_user_orders(current_user: User = Depends(get_current_user)):
    """Fetch order history for authenticated user."""
    orders = await Order.find(Order.userId == str(current_user.id)).sort("-created_at").to_list()

    items = [
        OrderResponse(
            id=o.orderId,
            date=o.date,
            status=o.status,
            totalPrice=o.totalPrice,
            paymentStatus=o.paymentStatus,
            paymentMethod=o.paymentMethod,
            receiptUrl=o.receiptUrl,
            rejectionReason=o.rejectionReason,
            items=[item.model_dump() for item in o.items],
            shippingAddress=o.shippingAddress.model_dump() if o.shippingAddress else None,
        ).model_dump()
        for o in orders
    ]

    return success_response(data=items, message="تاریخچه سفارش‌ها دریافت شد")


@router.get("/track/{order_id}", summary="Track order by numeric ID or ORD code")
async def track_order(order_id: str):
    """Public order tracking endpoint returning order timeline steps."""
    clean_id = order_id.strip()
    if not clean_id.startswith("ORD-") and clean_id.isdigit():
        clean_id = f"ORD-{clean_id}"

    order = await Order.find_one(Order.orderId == clean_id)
    if not order:
        order = await Order.find_one(Order.orderId == order_id.strip())

    if not order:
        return error_response(
            message="سفارشی با این کد یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    # Generate timeline steps based on order status and payment status
    status_order = ["pending", "processing", "shipped", "delivered"]
    curr_idx = status_order.index(order.status) if order.status in status_order else 0

    steps = [
        TrackingStep(
            title="statusReceived",
            desc="سفارش در سیستم ثبت شده است",
            completed=True,
        ),
        TrackingStep(
            title="statusPaymentReview",
            desc="بررسی فیش واریز کارت به کارت توسط مدیریت",
            completed=order.paymentStatus == "payment_approved" or curr_idx >= 1,
        ),
        TrackingStep(
            title="statusProcessing",
            desc="اثر هنری با بسته‌بندی تخصصی گالری در حال آماده‌سازی",
            completed=curr_idx >= 1,
        ),
        TrackingStep(
            title="statusShipped",
            desc="تحویل به پست پیشتاز یا پیک اختصاصی گالری",
            completed=curr_idx >= 2,
        ),
        TrackingStep(
            title="statusDelivered",
            desc="اثر هنری تحویل داده شده است",
            completed=curr_idx >= 3,
        ),
    ]

    data = OrderTrackingResponse(
        orderId=order.orderId,
        status=order.status,
        paymentStatus=order.paymentStatus,
        date=order.date,
        totalPrice=order.totalPrice,
        receiptUrl=order.receiptUrl,
        rejectionReason=order.rejectionReason,
        steps=[s.model_dump() for s in steps],
    ).model_dump()

    return success_response(data=data, message="وضعیت سفارش دریافت شد")


@router.get("/{id}", summary="Get order details")
async def get_order_details(
    id: str,
    current_user: User = Depends(get_current_user),
):
    """Fetch single order by orderId for authenticated owner or admin."""
    clean_id = id.strip()
    if not clean_id.startswith("ORD-") and clean_id.isdigit():
        clean_id = f"ORD-{clean_id}"

    order = await Order.find_one(Order.orderId == clean_id)
    if not order:
        try:
            order = await Order.get(PydanticObjectId(id))
        except Exception:
            pass

    if not order:
        return error_response(
            message="سفارش یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    # Authorization check
    if order.userId != str(current_user.id) and not current_user.is_admin_user:
        return error_response(
            message="شما دسترسی به این سفارش ندارید",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    data = OrderResponse(
        id=order.orderId,
        date=order.date,
        status=order.status,
        totalPrice=order.totalPrice,
        paymentStatus=order.paymentStatus,
        paymentMethod=order.paymentMethod,
        receiptUrl=order.receiptUrl,
        rejectionReason=order.rejectionReason,
        items=[item.model_dump() for item in order.items],
        shippingAddress=order.shippingAddress.model_dump() if order.shippingAddress else None,
    ).model_dump()

    return success_response(data=data, message="جزئیات سفارش دریافت شد")

