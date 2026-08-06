"""FAQ Router."""

from fastapi import APIRouter

from models.faq import FAQ
from schemas.faq import FAQResponse
from schemas.response import success_response

router = APIRouter()


@router.get("", summary="Get FAQ list")
@router.get("/", include_in_schema=False)
async def list_faqs():
    """Retrieve list of frequently asked questions."""
    faqs = await FAQ.find_all().sort("+order").to_list()

    items = [
        FAQResponse(
            id=str(f.id),
            q=f.question,
            a=f.answer,
        ).model_dump()
        for f in faqs
    ]

    return success_response(data=items, message="سوالات متداول دریافت شد")
