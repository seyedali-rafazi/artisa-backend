"""Favorites Router."""

from typing import List, Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from core.security import get_current_user
from models.favorite import Favorite
from models.product import Product
from models.user import User
from schemas.product import ProductResponse
from schemas.response import success_response

router = APIRouter()


async def get_product_or_none(product_id: str) -> Optional[Product]:
    """Helper to fetch a product by PydanticObjectId or string _id."""
    try:
        p = await Product.get(PydanticObjectId(product_id))
        if p:
            return p
    except Exception:
        pass
    return await Product.find_one({"_id": product_id})


@router.get("", summary="Get user favorite products")
@router.get("/", include_in_schema=False)
async def get_favorites(current_user: User = Depends(get_current_user)):
    """Fetch all favorite products for the current authenticated user."""
    user_id = str(current_user.id)
    favorites = await Favorite.find(Favorite.user_id == user_id).to_list()

    if not favorites:
        return success_response(data=[], message="لیست علاقه‌مندی‌ها خالی است")

    product_ids = [f.product_id for f in favorites]

    # Convert valid object IDs for batch lookup
    object_ids = []
    str_ids = []
    for pid in product_ids:
        try:
            object_ids.append(PydanticObjectId(pid))
        except Exception:
            str_ids.append(pid)

    query_conditions = []
    if object_ids:
        query_conditions.append({"_id": {"$in": object_ids}})
    if str_ids:
        query_conditions.append({"_id": {"$in": str_ids}})

    if not query_conditions:
        return success_response(data=[], message="لیست علاقه‌مندی‌ها با موفقیت دریافت شد")

    if len(query_conditions) == 1:
        find_query = query_conditions[0]
    else:
        find_query = {"$or": query_conditions}

    products = await Product.find(find_query).to_list()

    items = [
        ProductResponse(
            id=str(p.id),
            name=p.name,
            nameEn=p.nameEn,
            price=p.price,
            oldPrice=p.oldPrice,
            image=p.image,
            category=p.category,
            categoryEn=p.categoryEn,
            rating=p.rating,
            isSpecial=p.isSpecial,
            isBestSeller=p.isBestSeller,
            description=p.description,
            descriptionEn=p.descriptionEn,
            specifications=p.specifications or {},
        ).model_dump()
        for p in products
    ]

    return success_response(data=items, message="لیست علاقه‌مندی‌ها با موفقیت دریافت شد")


@router.get("/ids", summary="Get user favorite product IDs")
async def get_favorite_ids(current_user: User = Depends(get_current_user)):
    """Fetch array of favorited product IDs for fast O(1) status lookup."""
    user_id = str(current_user.id)
    favorites = await Favorite.find(Favorite.user_id == user_id).to_list()
    favorite_ids = [f.product_id for f in favorites]
    return success_response(
        data={"favorite_ids": favorite_ids},
        message="شناسه‌های علاقه‌مندی با موفقیت دریافت شد",
    )


@router.get("/{product_id}/status", summary="Check if product is favorited")
async def get_favorite_status(
    product_id: str, current_user: User = Depends(get_current_user)
):
    """Check whether a specific product is favorited by current user."""
    user_id = str(current_user.id)
    existing = await Favorite.find_one(
        Favorite.user_id == user_id, Favorite.product_id == product_id
    )
    is_favorited = existing is not None
    return success_response(
        data={"is_favorited": is_favorited, "product_id": product_id},
        message="وضعیت علاقه‌مندی دریافت شد",
    )


@router.post("/{product_id}", summary="Add product to favorites")
async def add_favorite(
    product_id: str, current_user: User = Depends(get_current_user)
):
    """Add a product to user favorites."""
    user_id = str(current_user.id)

    # Validate product exists
    product = await get_product_or_none(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="محصول مورد نظر یافت نشد",
        )

    # Check if already favorited
    existing = await Favorite.find_one(
        Favorite.user_id == user_id, Favorite.product_id == product_id
    )
    if existing:
        return success_response(
            data={"is_favorited": True, "product_id": product_id},
            message="محصول قبلاً در علاقه‌مندی‌ها وجود دارد",
        )

    try:
        fav = Favorite(user_id=user_id, product_id=product_id)
        await fav.insert()
    except DuplicateKeyError:
        pass
    except Exception as e:
        if "duplicate key" in str(e).lower() or "11000" in str(e):
            pass
        else:
            raise e

    return success_response(
        data={"is_favorited": True, "product_id": product_id},
        message="محصول به علاقه‌مندی‌ها اضافه شد",
        status_code=status.HTTP_201_CREATED,
    )


@router.delete("/{product_id}", summary="Remove product from favorites")
async def remove_favorite(
    product_id: str, current_user: User = Depends(get_current_user)
):
    """Remove a product from user favorites."""
    user_id = str(current_user.id)

    existing = await Favorite.find_one(
        Favorite.user_id == user_id, Favorite.product_id == product_id
    )
    if existing:
        await existing.delete()

    return success_response(
        data={"is_favorited": False, "product_id": product_id},
        message="محصول از علاقه‌مندی‌ها حذف شد",
    )
