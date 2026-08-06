"""Blog Article Schemas."""

from typing import Optional
from pydantic import BaseModel


class ArticleResponse(BaseModel):
    id: str
    title: str
    desc: str
    content: Optional[str] = None
    date: str
    author: str
    image: str
