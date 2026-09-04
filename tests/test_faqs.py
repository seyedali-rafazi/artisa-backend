"""Unit and schema tests for FAQ Management functionality."""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from bson import ObjectId
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from models.faq import FAQ
from schemas.faq import (
    FAQResponse,
    FAQCreateRequest,
    FAQUpdateRequest,
    FAQReorderRequest,
    FAQReorderItem,
)
from api.v1.faqs import serialize_faq


class TestFAQSchemas(unittest.TestCase):
    """Test validation and serialization of FAQ schemas."""

    def test_faq_create_validation_success(self):
        """Valid payload creates FAQCreateRequest successfully."""
        req = FAQCreateRequest(
            question="آیا امکان خرید قسطی وجود دارد؟",
            answer="بله، از طریق درگاه‌های اسنپ‌پی و تپسی‌پی امکان پرداخت اقساطی فراهم است.",
            order=3,
            is_active=True,
        )
        self.assertEqual(req.question, "آیا امکان خرید قسطی وجود دارد؟")
        self.assertEqual(req.order, 3)
        self.assertTrue(req.is_active)

    def test_faq_create_validation_too_short(self):
        """Short question or answer raises ValidationError."""
        with self.assertRaises(ValidationError):
            FAQCreateRequest(question="a", answer="جواب معتبر")

        with self.assertRaises(ValidationError):
            FAQCreateRequest(question="سوال معتبر", answer="a")

    def test_faq_reorder_schema(self):
        """Reorder request accepts multiple items with id and order."""
        req = FAQReorderRequest(
            items=[
                FAQReorderItem(id="66d8b9e11122334455667788", order=1),
                FAQReorderItem(id="66d8b9e11122334455667789", order=2),
            ]
        )
        self.assertEqual(len(req.items), 2)
        self.assertEqual(req.items[0].order, 1)

    def test_serialize_faq_dual_fields(self):
        """serialize_faq maps document to schema with dual field names (question/q and answer/a)."""
        from unittest.mock import MagicMock
        mock_faq = MagicMock()
        mock_faq.id = ObjectId()
        mock_faq.question = "چگونه سفارش خود را رهگیری کنم؟"
        mock_faq.answer = "از منوی بالای سایت، بخش پیگیری سفارش را انتخاب کرده و کد سفارش را وارد کنید."
        mock_faq.order = 2
        mock_faq.is_active = True
        mock_faq.created_at = datetime.utcnow()
        mock_faq.updated_at = datetime.utcnow()

        serialized = serialize_faq(mock_faq)
        self.assertEqual(serialized.id, str(mock_faq.id))
        self.assertEqual(serialized.question, mock_faq.question)
        self.assertEqual(serialized.q, mock_faq.question)
        self.assertEqual(serialized.answer, mock_faq.answer)
        self.assertEqual(serialized.a, mock_faq.answer)
        self.assertEqual(serialized.order, 2)
        self.assertTrue(serialized.is_active)

    def test_serialize_faq_legacy_fallback(self):
        """Handles legacy documents missing timestamps or is_active safely."""
        from unittest.mock import MagicMock
        mock_faq = MagicMock()
        mock_faq.id = ObjectId()
        mock_faq.question = "سوال قدیمی"
        mock_faq.answer = "پاسخ قدیمی"
        mock_faq.order = 0
        mock_faq.is_active = True
        mock_faq.created_at = None
        mock_faq.updated_at = None

        serialized = serialize_faq(mock_faq)
        self.assertEqual(serialized.question, "سوال قدیمی")
        self.assertEqual(serialized.q, "سوال قدیمی")
        self.assertEqual(serialized.answer, "پاسخ قدیمی")
        self.assertEqual(serialized.a, "پاسخ قدیمی")
        self.assertTrue(serialized.is_active)
        self.assertEqual(serialized.order, 0)


if __name__ == "__main__":
    unittest.main()
