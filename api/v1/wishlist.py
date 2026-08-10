"""Wishlist Router (Legacy & Alias endpoints for Favorites)."""

from fastapi import APIRouter, Depends
from core.security import get_current_user
from models.user import User
from api.v1.favorites import (
    get_favorites as get_favs_endpoint,
    add_favorite as add_fav_endpoint,
    remove_favorite as remove_fav_endpoint,
    get_favorite_status as status_fav_endpoint,
)
from models.favorite import Favorite

router = APIRouter()


@router.get("", summary="Get user wishlist items")
@router.get("/", include_in_schema=False)
async def get_wishlist(current_user: User = Depends(get_current_user)):
    """Fetch user wishlist products."""
    return await get_favs_endpoint(current_user=current_user)


@router.post("/toggle/{product_id}", summary="Toggle product in user wishlist")
async def toggle_wishlist_item(
    product_id: str, current_user: User = Depends(get_current_user)
):
    """Add or remove product from user wishlist."""
    user_id = str(current_user.id)
    existing = await Favorite.find_one(
        Favorite.user_id == user_id, Favorite.product_id == product_id
    )

    if existing:
        res = await remove_fav_endpoint(product_id=product_id, current_user=current_user)
        return res
    else:
        res = await add_fav_endpoint(product_id=product_id, current_user=current_user)
        return res
