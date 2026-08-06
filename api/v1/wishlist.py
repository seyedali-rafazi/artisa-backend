"""Wishlist Router."""

from fastapi import APIRouter, Depends, status

from core.security import get_current_user
from models.product import Product
from models.user import User
from models.wishlist import Wishlist
from schemas.product import ProductResponse
from schemas.response import success_response, error_response

router = APIRouter()


@router.get("", summary="Get user wishlist items")
@router.get("/", include_in_schema=False)
async def get_wishlist(current_user: User = Depends(get_current_user)):
    """Fetch user wishlist products."""
    user_id = str(current_user.id)
    wishlist = await Wishlist.find_one(Wishlist.userId == user_id)

    if not wishlist or not wishlist.productIds:
        return success_response(data=[], message="علاقه‌مندی‌ها دریافت شد")

    # Fetch products
    products = []
    for pid in wishlist.productIds:
        p = None
        try:
            from beanie import PydanticObjectId

            p = await Product.get(PydanticObjectId(pid))
        except Exception:
            p = await Product.find_one({"_id": pid})
        if p:
            products.append(
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
            )

    return success_response(data=products, message="علاقه‌مندی‌ها دریافت شد")


@router.post("/toggle/{product_id}", summary="Toggle product in user wishlist")
async def toggle_wishlist_item(
    product_id: str, current_user: User = Depends(get_current_user)
):
    """Add or remove product from user wishlist."""
    user_id = str(current_user.id)
    wishlist = await Wishlist.find_one(Wishlist.userId == user_id)

    if not wishlist:
        wishlist = Wishlist(userId=user_id, productIds=[])
        await wishlist.insert()

    added = False
    if product_id in wishlist.productIds:
        wishlist.productIds.remove(product_id)
        msg = "محصول از علاقه‌مندی‌ها حذف شد"
    else:
        wishlist.productIds.append(product_id)
        added = True
        msg = "محصول به علاقه‌مندی‌ها اضافه شد"

    await wishlist.save()
    return success_response(data={"added": added}, message=msg)
