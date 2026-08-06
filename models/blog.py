"""Blog Article Document Model."""

from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field


class Article(Document):
    """Blog Article model."""

    articleId: str
    title: str
    desc: str
    content: Optional[str] = None
    date: str
    author: str
    image: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "articles"
