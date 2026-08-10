"""Unit tests for Favorites model, schemas, and logic (pure unit test without live DB requirement)."""

import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock
from bson import ObjectId
from beanie.odm.documents import DocumentSettings

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from models.favorite import Favorite
from schemas.favorite import (
    FavoriteStatusResponse,
    FavoriteActionResponse,
    FavoriteIdsResponse,
)

# Mock document settings using model_construct to bypass runtime type validation for unit testing
Favorite._document_settings = DocumentSettings.model_construct(
    name="favorites",
    pymongo_collection=MagicMock(),
    use_state_management=False,
)


def test_favorite_model_instantiation():
    """Verify Favorite model instantiation and default fields."""
    user_id = str(ObjectId())
    product_id = str(ObjectId())

    fav = Favorite(user_id=user_id, product_id=product_id)
    assert fav.user_id == user_id
    assert fav.product_id == product_id
    assert isinstance(fav.created_at, datetime)


def test_favorite_schemas_validation():
    """Verify Pydantic schemas for Favorite responses."""
    pid = str(ObjectId())

    # Status response
    status_resp = FavoriteStatusResponse(is_favorited=True, product_id=pid)
    assert status_resp.is_favorited is True
    assert status_resp.product_id == pid

    # Action response
    action_resp = FavoriteActionResponse(
        is_favorited=True, product_id=pid, message="محصول اضافه شد"
    )
    assert action_resp.is_favorited is True
    assert action_resp.message == "محصول اضافه شد"

    # IDs list response
    ids_resp = FavoriteIdsResponse(favorite_ids=[pid, "pid_2"])
    assert len(ids_resp.favorite_ids) == 2
    assert pid in ids_resp.favorite_ids
