"""Comments and Reviews Router."""

from datetime import datetime
from typing import Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from core.security import get_current_user
from models.comment import Comment
from models.product import Product
from models.user import User
from schemas.comment import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    PaginatedCommentsResponse,
)
from schemas.response import success_response, error_response

router = APIRouter()


async def recalculate_product_rating(product_id: str):
    """Helper to update average rating on product document."""
    try:
        product = await Product.get(PydanticObjectId(product_id))
        if not product:
            return
        comments = await Comment.find(
            Comment.productId == product_id,
            Comment.is_deleted == False,
            Comment.status == "approved",
        ).to_list()
        if comments:
            avg_rating = sum(c.rating for c in comments) / len(comments)
            product.rating = round(avg_rating, 1)
        else:
            product.rating = 5.0
        product.updated_at = datetime.utcnow()
        await product.save()
    except Exception:
        pass


@router.get("/products/{product_id}/comments", summary="Get comments for a product")
async def get_product_comments(
    product_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    """Retrieve paginated comments/reviews for a given product."""
    skip = (page - 1) * limit
    query = Comment.find(
        Comment.productId == product_id,
        Comment.is_deleted == False,
        Comment.status == "approved",
    ).sort("-created_at")

    total = await query.count()
    comments = await query.skip(skip).limit(limit).to_list()

    items = [
        CommentResponse(
            id=str(c.id),
            productId=c.productId,
            userId=c.userId,
            userName=c.userName,
            userEmail=c.userEmail,
            text=c.text,
            rating=c.rating,
            status=c.status,
            date=c.date,
            created_at=c.created_at,
        )
        for c in comments
    ]

    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    paginated_data = PaginatedCommentsResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    ).model_dump()

    return success_response(data=paginated_data, message="نظرات محصول دریافت شد")


@router.post("/products/{product_id}/comments", summary="Add a comment to a product")
async def add_product_comment(
    product_id: str,
    payload: CommentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Post a comment for a product (requires authentication)."""
    # Verify product existence
    try:
        product = await Product.get(PydanticObjectId(product_id))
    except Exception:
        product = None

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="محصول مورد نظر یافت نشد",
        )

    user_id = str(current_user.id)

    # Check for duplicate comment content by user on same product
    recent_duplicate = await Comment.find_one(
        Comment.productId == product_id,
        Comment.userId == user_id,
        Comment.text == payload.text,
        Comment.is_deleted == False,
    )
    if recent_duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="شما قبلاً این نظر را برای این محصول ثبت کرده‌اید.",
        )

    comment = Comment(
        productId=product_id,
        userId=user_id,
        userName=payload.name if payload.name else current_user.name,
        userEmail=current_user.email,
        text=payload.text,
        rating=payload.rating,
        status="approved",
        is_deleted=False,
        date=datetime.now().strftime("%Y/%m/%d"),
    )
    await comment.insert()

    # Recalculate product rating
    await recalculate_product_rating(product_id)

    data = CommentResponse(
        id=str(comment.id),
        productId=comment.productId,
        userId=comment.userId,
        userName=comment.userName,
        userEmail=comment.userEmail,
        text=comment.text,
        rating=comment.rating,
        status=comment.status,
        date=comment.date,
        created_at=comment.created_at,
    ).model_dump()

    return success_response(
        data=data,
        message="نظر شما با موفقیت ثبت شد",
        status_code=status.HTTP_201_CREATED,
    )


@router.patch("/comments/{comment_id}", summary="Update comment")
async def update_comment(
    comment_id: str,
    payload: CommentUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a comment (Owner or Admin)."""
    try:
        comment = await Comment.get(PydanticObjectId(comment_id))
    except Exception:
        comment = None

    if not comment or comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="نظر مورد نظر یافت نشد",
        )

    # Ownership check
    is_owner = comment.userId == str(current_user.id)
    if not is_owner and not current_user.is_admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما اجازه ویرایش این نظر را ندارید",
        )

    if payload.text is not None:
        comment.text = payload.text
    if payload.rating is not None:
        comment.rating = payload.rating

    comment.updated_at = datetime.utcnow()
    await comment.save()

    # Recalculate product rating
    await recalculate_product_rating(comment.productId)

    data = CommentResponse(
        id=str(comment.id),
        productId=comment.productId,
        userId=comment.userId,
        userName=comment.userName,
        userEmail=comment.userEmail,
        text=comment.text,
        rating=comment.rating,
        status=comment.status,
        date=comment.date,
        created_at=comment.created_at,
    ).model_dump()

    return success_response(data=data, message="نظر با موفقیت بروزرسانی شد")


@router.delete("/comments/{comment_id}", summary="Delete comment")
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete (soft-delete) a comment (Owner or Admin)."""
    try:
        comment = await Comment.get(PydanticObjectId(comment_id))
    except Exception:
        comment = None

    if not comment or comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="نظر مورد نظر یافت نشد",
        )

    # Ownership check
    is_owner = comment.userId == str(current_user.id)
    if not is_owner and not current_user.is_admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما اجازه حذف این نظر را ندارید",
        )

    comment.is_deleted = True
    comment.updated_at = datetime.utcnow()
    await comment.save()

    # Recalculate product rating
    await recalculate_product_rating(comment.productId)

    return success_response(message="نظر با موفقیت حذف شد")
