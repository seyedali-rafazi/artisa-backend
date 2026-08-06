"""Banner Schemas."""

from pydantic import BaseModel


class BannerResponse(BaseModel):
    id: str
    title: str
    subtitle: str
    badge: str
    buttonText: str
    image: str
    link: str
