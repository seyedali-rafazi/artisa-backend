"""API V1 Package initialization."""

from api.v1.auth import router as auth_router
from api.v1.users import router as users_router
from api.v1.products import router as products_router
from api.v1.comments import router as comments_router
from api.v1.addresses import router as addresses_router
from api.v1.orders import router as orders_router
from api.v1.wishlist import router as wishlist_router
from api.v1.favorites import router as favorites_router
from api.v1.blog import router as blog_router
from api.v1.faqs import router as faqs_router
from api.v1.banners import router as banners_router
from api.v1.uploads import router as uploads_router
from api.v1.admin import router as admin_router
from api.v1.special_offers import (
    public_router as special_offers_router,
    admin_special_offers_router,
)

__all__ = [
    "auth_router",
    "users_router",
    "products_router",
    "comments_router",
    "addresses_router",
    "orders_router",
    "wishlist_router",
    "favorites_router",
    "blog_router",
    "faqs_router",
    "banners_router",
    "uploads_router",
    "admin_router",
    "special_offers_router",
    "admin_special_offers_router",
]
