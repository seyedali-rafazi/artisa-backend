"""Banners Router."""

from fastapi import APIRouter

from models.banner import Banner
from schemas.banner import BannerResponse
from schemas.response import success_response

router = APIRouter()


@router.get("", summary="Get home hero slider banners")
@router.get("/", include_in_schema=False)
async def list_banners():
    """Retrieve list of hero slider banners."""
    banners = await Banner.find_all().sort("+order").to_list()

    items = [
        BannerResponse(
            id=str(b.id),
            title=b.title,
            subtitle=b.subtitle,
            badge=b.badge,
            buttonText=b.buttonText,
            image=b.image,
            link=b.link,
        ).model_dump()
        for b in banners
    ]

    return success_response(data=items, message="بنرهای صفحه اصلی دریافت شد")
