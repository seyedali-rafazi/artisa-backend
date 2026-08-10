"""Unit tests for Comments model, schemas, XSS sanitization, and Pydantic validators."""

import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from bson import ObjectId
from beanie.odm.documents import DocumentSettings

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from models.comment import Comment
from schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentAdminUpdate,
    CommentResponse,
    PaginatedCommentsResponse,
)

# Mock document settings for unit testing without live DB
Comment._document_settings = DocumentSettings.model_construct(
    name="comments",
    pymongo_collection=MagicMock(),
    use_state_management=False,
)


def test_comment_model_instantiation():
    """Verify Comment model fields and defaults."""
    pid = str(ObjectId())
    uid = str(ObjectId())

    comment = Comment(
        productId=pid,
        userId=uid,
        userName="تست کننده",
        userEmail="test@example.com",
        text="نظر آزمایش عالی",
        rating=5,
    )

    assert comment.productId == pid
    assert comment.userId == uid
    assert comment.userName == "تست کننده"
    assert comment.text == "نظر آزمایش عالی"
    assert comment.rating == 5
    assert comment.status == "approved"
    assert comment.is_deleted is False


def test_comment_create_schema_validation_and_xss_escape():
    """Verify CommentCreate trims text, validates length, and escapes HTML tags."""
    # Valid input with leading/trailing spaces
    payload = CommentCreate(text="   عالی و باکیفیت بود   ", rating=5)
    assert payload.text == "عالی و باکیفیت بود"
    assert payload.rating == 5

    # HTML injection payload -> must be html escaped
    xss_payload = CommentCreate(text="<script>alert('hack')</script> با تشکر", rating=4)
    assert "<script>" not in xss_payload.text
    assert "&lt;script&gt;alert(&#x27;hack&#x27;)&lt;/script&gt; با تشکر" == xss_payload.text

    # Too short text (< 3 chars)
    with pytest.raises(Exception):
        CommentCreate(text="یا", rating=5)

    # Invalid rating (> 5)
    with pytest.raises(Exception):
        CommentCreate(text="متن تست برای امتیاز", rating=10)


def test_comment_admin_update_schema():
    """Verify CommentAdminUpdate validates moderation status."""
    # Valid status
    admin_up = CommentAdminUpdate(status="rejected")
    assert admin_up.status == "rejected"

    # Invalid status
    with pytest.raises(Exception):
        CommentAdminUpdate(status="invalid_status")


def test_paginated_comments_response_schema():
    """Verify PaginatedCommentsResponse structure."""
    cid = str(ObjectId())
    pid = str(ObjectId())
    c_resp = CommentResponse(
        id=cid,
        productId=pid,
        userName="علی رضایی",
        text="بسیار عالی",
        rating=5,
        status="approved",
        date="1403/05/20",
    )

    paginated = PaginatedCommentsResponse(
        items=[c_resp],
        total=1,
        page=1,
        limit=10,
        total_pages=1,
    )

    assert paginated.total == 1
    assert paginated.items[0].id == cid
    assert paginated.items[0].userName == "علی رضایی"
