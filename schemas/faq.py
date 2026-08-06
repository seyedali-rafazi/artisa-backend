"""FAQ Schemas."""

from pydantic import BaseModel


class FAQResponse(BaseModel):
    id: str
    q: str
    a: str
