"""Favorite Schemas."""

from typing import List
from pydantic import BaseModel


class FavoriteStatusResponse(BaseModel):
    """Schema for single product favorite status response."""

    is_favorited: bool
    product_id: str


class FavoriteActionResponse(BaseModel):
    """Schema for favorite add/remove action response."""

    is_favorited: bool
    product_id: str
    message: str


class FavoriteIdsResponse(BaseModel):
    """Schema for user's favorite product IDs response."""

    favorite_ids: List[str]
