"""Orders Router."""

import random
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, status

from core.security import get_optional_user, get_current_user
from models.order import Order, OrderItem, ShippingAddress
from models.user import User
from schemas.order import OrderCreate, OrderResponse, OrderTrackingResponse, TrackingStep
from schemas.response import success_response, error_response

router = APIRouter()


@router.post("", summary="Create order (Checkout)")
@router.post("/", include_in_schema=False)
async def create_order(
    payload: OrderCreate,
    optional_user: Optional[User] = Depends(get_optional_user),
):
    """Place a new order upon checkout."""
    if not payload.items or len(payload.items) == 0:
        return error_response(
            message="سبد خرید خالی است", status_code=status.HTTP_400_BAD_REQUEST
        )

    # Generate 6-digit numeric order code
    numeric_code = str(random.randint(100000, 999999))
    order_id = f"ORD-{numeric_code}"

    items_models = [
        OrderItem(
            id=item.id,
            name=item.name,
            price=item.price,
            quantity=item.quantity,
            image=item.image,
        )
        for item in payload.items
    ]

    total_price = sum(item.price * item.quantity for item in payload.items)

    shipping_info = ShippingAddress(
        fullName=payload.fullName,
        phone=payload.phone,
        postalCode=payload.postalCode,
        address=payload.address,
    )

    order = Order(
        orderId=order_id,
        userId=str(optional_user.id) if optional_user else None,
        date=datetime.now().strftime("%Y/%m/%d"),
        status="processing",
        totalPrice=total_price,
        paymentStatus="paid",
        paymentMethod=payload.paymentMethod,
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
        items=[item.model_dump() for item in payload.items],
        shippingAddress=shipping_info.model_dump(),
    ).model_dump()

    return success_response(
        data=data,
        message="سفارش با موفقیت ثبت شد",
        status_code=status.HTTP_201_CREATED,
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
        # Fallback query by exact orderId
        order = await Order.find_one(Order.orderId == order_id.strip())

    if not order:
        return error_response(
            message="سفارشی با این کد یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    # Generate timeline steps based on order.status
    status_order = ["pending", "processing", "shipped", "delivered"]
    curr_idx = status_order.index(order.status) if order.status in status_order else 1

    steps = [
        TrackingStep(
            title="statusReceived",
            desc="سفارش در سیستم ثبت شده است",
            completed=curr_idx >= 0,
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
            desc="اثر هنری درب منزل تحویل داده شده است",
            completed=curr_idx >= 3,
        ),
    ]

    data = OrderTrackingResponse(
        orderId=order.orderId,
        status=order.status,
        date=order.date,
        totalPrice=order.totalPrice,
        steps=[s.model_dump() for s in steps],
    ).model_dump()

    return success_response(data=data, message="وضعیت سفارش دریافت شد")


@router.get("/{id}", summary="Get order details")
async def get_order_details(id: str):
    """Fetch single order by orderId."""
    order = await Order.find_one(Order.orderId == id)
    if not order:
        try:
            from beanie import PydanticObjectId

            order = await Order.get(PydanticObjectId(id))
        except Exception:
            pass

    if not order:
        return error_response(
            message="سفارش یافت نشد", status_code=status.HTTP_404_NOT_FOUND
        )

    data = OrderResponse(
        id=order.orderId,
        date=order.date,
        status=order.status,
        totalPrice=order.totalPrice,
        paymentStatus=order.paymentStatus,
        paymentMethod=order.paymentMethod,
        items=[item.model_dump() for item in order.items],
        shippingAddress=order.shippingAddress.model_dump() if order.shippingAddress else None,
    ).model_dump()

    return success_response(data=data, message="جزئیات سفارش دریافت شد")
