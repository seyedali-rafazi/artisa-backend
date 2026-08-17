"""Unit tests for Comments model, schemas, XSS sanitization, and Pydantic validators."""

import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock
from bson import ObjectId
from beanie.odm.documents import DocumentSettings

try:
    import pytest
except ImportError:
    class _PytestMock:
        @staticmethod
        def raises(exc_type):
            class _RaisesContext:
                def __enter__(self):
                    return self
                def __exit__(self, exc_type_val, exc_val, exc_tb):
                    if not exc_type_val or not issubclass(exc_type_val, exc_type):
                        raise AssertionError(f"Expected exception {exc_type} but got {exc_type_val}")
                    return True
            return _RaisesContext()
    pytest = _PytestMock()

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


class TestCommentsUnit(unittest.TestCase):
    """Unit tests for Comments model and schemas."""

    def test_comment_model_instantiation(self):
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

        self.assertEqual(comment.productId, pid)
        self.assertEqual(comment.userId, uid)
        self.assertEqual(comment.userName, "تست کننده")
        self.assertEqual(comment.text, "نظر آزمایش عالی")
        self.assertEqual(comment.rating, 5)
        self.assertEqual(comment.status, "approved")
        self.assertFalse(comment.is_deleted)

    def test_comment_create_schema_validation_and_xss_escape(self):
        """Verify CommentCreate trims text, validates length, and escapes HTML tags."""
        # Valid input with leading/trailing spaces
        payload = CommentCreate(text="   عالی و باکیفیت بود   ", rating=5)
        self.assertEqual(payload.text, "عالی و باکیفیت بود")
        self.assertEqual(payload.rating, 5)

        # HTML injection payload -> must be html escaped
        xss_payload = CommentCreate(text="<script>alert('hack')</script> با تشکر", rating=4)
        self.assertNotIn("<script>", xss_payload.text)
        self.assertEqual("&lt;script&gt;alert(&#x27;hack&#x27;)&lt;/script&gt; با تشکر", xss_payload.text)

        # Too short text (< 3 chars)
        with pytest.raises(Exception):
            CommentCreate(text="یا", rating=5)

        # Invalid rating (> 5)
        with pytest.raises(Exception):
            CommentCreate(text="متن تست برای امتیاز", rating=10)

    def test_comment_admin_update_schema(self):
        """Verify CommentAdminUpdate validates moderation status."""
        # Valid status
        admin_up = CommentAdminUpdate(status="rejected")
        self.assertEqual(admin_up.status, "rejected")

        # Invalid status
        with pytest.raises(Exception):
            CommentAdminUpdate(status="invalid_status")

    def test_paginated_comments_response_schema(self):
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

        self.assertEqual(paginated.total, 1)
        self.assertEqual(paginated.items[0].id, cid)
        self.assertEqual(paginated.items[0].userName, "علی رضایی")


if __name__ == "__main__":
    unittest.main()
