"""Comment Pydantic Schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1)
    rating: int = Field(default=5, ge=1, le=5)
    name: Optional[str] = None


class CommentResponse(BaseModel):
    id: str
    productId: str
    userName: str
    text: str
    rating: int
    date: str
