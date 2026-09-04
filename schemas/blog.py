"""Blog Article Schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ArticleCreateRequest(BaseModel):
    """Schema for creating a blog article."""

    title: str = Field(..., min_length=2, max_length=300, description="Article title")
    desc: Optional[str] = Field(None, description="Short summary/excerpt of the article")
    content: Optional[str] = Field(None, description="Full rich text/HTML article content")
    image: str = Field(..., description="Cover/banner image URL")
    author: Optional[str] = Field(None, description="Author name")
    date: Optional[str] = Field(None, description="Shamsi/Persian publication date")


class ArticleUpdateRequest(BaseModel):
    """Schema for updating an existing blog article."""

    title: Optional[str] = Field(None, min_length=2, max_length=300)
    desc: Optional[str] = None
    content: Optional[str] = None
    image: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None


class ArticleResponse(BaseModel):
    """Public schema for returning article data."""

    id: str
    articleId: Optional[str] = None
    title: str
    desc: str
    content: Optional[str] = None
    date: str
    author: str
    image: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginatedArticlesResponse(BaseModel):
    """Paginated list response for articles."""

    items: List[ArticleResponse]
    total: int
    page: int
    limit: int
    total_pages: int
