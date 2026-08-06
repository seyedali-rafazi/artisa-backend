"""Comments and Reviews Router."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, status

from core.security import get_optional_user
from models.comment import Comment
from models.user import User
from schemas.comment import CommentCreate, CommentResponse
from schemas.response import success_response, error_response

router = APIRouter()


@router.get("/{product_id}/comments", summary="Get comments for a product")
async def get_product_comments(product_id: str):
    """Retrieve all comments/reviews for a given product."""
    comments = await Comment.find(Comment.productId == product_id).sort("-created_at").to_list()

    items = [
        CommentResponse(
            id=str(c.id),
            productId=c.productId,
            userName=c.userName,
            text=c.text,
            rating=c.rating,
            date=c.date,
        ).model_dump()
        for c in comments
    ]

    return success_response(data=items, message="نظرات محصول دریافت شد")


@router.post("/{product_id}/comments", summary="Add a comment to a product")
async def add_product_comment(
    product_id: str,
    payload: CommentCreate,
    request: Request,
    optional_user: Optional[User] = Depends(get_optional_user),
):
    """Post a comment for a product (guest or logged-in user)."""
    user_name = payload.name if payload.name else ("کاربر مهمان" if not optional_user else optional_user.name)

    comment = Comment(
        productId=product_id,
        userId=str(optional_user.id) if optional_user else None,
        userName=user_name,
        text=payload.text,
        rating=payload.rating,
        date=datetime.now().strftime("%Y/%m/%d"),
    )
    await comment.insert()

    data = CommentResponse(
        id=str(comment.id),
        productId=comment.productId,
        userName=comment.userName,
        text=comment.text,
        rating=comment.rating,
        date=comment.date,
    ).model_dump()

    return success_response(
        data=data,
        message="نظر شما با موفقیت ثبت شد",
        status_code=status.HTTP_201_CREATED,
    )
