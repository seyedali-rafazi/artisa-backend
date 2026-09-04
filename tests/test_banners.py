"""Unit and schema tests for Banner Management functionality."""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from bson import ObjectId
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from models.banner import Banner, BannerTextElement, BannerPosition
from schemas.banner import (
    BannerPositionSchema,
    BannerTextElementSchema,
    BannerCreateRequest,
    BannerUpdateRequest,
    BannerReorderRequest,
    BannerReorderItem,
    BannerResponse,
)
from api.v1.banners import serialize_banner


class TestBannerSchemas(unittest.TestCase):
    """Test validation and serialization of Banner schemas."""

    def test_banner_position_valid(self):
        """Valid coordinates within 0 to 100 succeed."""
        pos = BannerPositionSchema(x=35.5, y=80.0)
        self.assertEqual(pos.x, 35.5)
        self.assertEqual(pos.y, 80.0)

    def test_banner_position_out_of_bounds(self):
        """Coordinates outside 0 to 100 raise ValidationError."""
        with self.assertRaises(ValidationError):
            BannerPositionSchema(x=-1.0, y=50.0)
        with self.assertRaises(ValidationError):
            BannerPositionSchema(x=50.0, y=101.0)

    def test_banner_text_element_valid(self):
        """Valid text element with position succeeds."""
        elem = BannerTextElementSchema(
            id="test-123",
            text="کالکشن تابستانه",
            fontFamily="Vazirmatn",
            fontSize=36,
            fontWeight="bold",
            color="#E8DCCB",
            textAlign="center",
            position=BannerPositionSchema(x=50.0, y=40.0),
        )
        self.assertEqual(elem.text, "کالکشن تابستانه")
        self.assertEqual(elem.fontSize, 36)
        self.assertEqual(elem.position.x, 50.0)

    def test_banner_text_element_empty_text(self):
        """Empty text string raises ValidationError."""
        with self.assertRaises(ValidationError):
            BannerTextElementSchema(
                text="",
                position=BannerPositionSchema(x=10.0, y=20.0),
            )

    def test_banner_create_request_success(self):
        """Valid BannerCreateRequest succeeds."""
        req = BannerCreateRequest(
            title="جشنواره فروش ویژه",
            image="https://example.public.blob.vercel-storage.com/banner.webp",
            texts=[
                BannerTextElementSchema(
                    text="تخفیف تا ۴۰٪",
                    position=BannerPositionSchema(x=50.0, y=50.0),
                )
            ],
            link="/products",
            linkOpenInNewTab=False,
            isActive=True,
            order=1,
        )
        self.assertEqual(req.title, "جشنواره فروش ویژه")
        self.assertEqual(len(req.texts), 1)
        self.assertEqual(req.texts[0].text, "تخفیف تا ۴۰٪")
        self.assertTrue(req.isActive)

    def test_banner_create_request_missing_required(self):
        """Missing title or image raises ValidationError."""
        with self.assertRaises(ValidationError):
            BannerCreateRequest(title="", image="https://example.com/img.jpg")
        with self.assertRaises(ValidationError):
            BannerCreateRequest(title="Valid Title", image="")

    def test_banner_reorder_request(self):
        """BannerReorderRequest requires non-empty items."""
        req = BannerReorderRequest(
            items=[
                BannerReorderItem(id="66d8b9e11122334455667788", order=1),
                BannerReorderItem(id="66d8b9e11122334455667789", order=2),
            ]
        )
        self.assertEqual(len(req.items), 2)
        with self.assertRaises(ValidationError):
            BannerReorderRequest(items=[])

    def test_serialize_modern_banner(self):
        """serialize_banner maps modern Banner document to BannerResponse correctly."""
        from unittest.mock import MagicMock
        mock_banner = MagicMock()
        mock_banner.id = ObjectId()
        mock_banner.title = "بنر مدرن"
        mock_banner.image = "https://blob.vercel-storage.com/modern.webp"
        mock_banner.link = "/special-offers"
        mock_banner.linkOpenInNewTab = True
        mock_banner.isActive = True
        mock_banner.order = 2
        mock_banner.created_at = datetime.utcnow()
        mock_banner.updated_at = datetime.utcnow()
        mock_banner.subtitle = "زیرعنوان"
        mock_banner.badge = "جدید"
        mock_banner.buttonText = "خرید"

        mock_text = MagicMock()
        mock_text.id = "txt-1"
        mock_text.text = "عنوان هنری"
        mock_text.fontFamily = "Vazirmatn"
        mock_text.fontSize = 32
        mock_text.fontWeight = "700"
        mock_text.color = "#FFFFFF"
        mock_text.textAlign = "center"
        mock_text.lineHeight = 1.4
        mock_text.letterSpacing = 0.0
        mock_text.textShadow = "0 2px 4px rgba(0,0,0,0.5)"
        mock_pos = MagicMock()
        mock_pos.x = 45.0
        mock_pos.y = 55.0
        mock_text.position = mock_pos
        mock_banner.texts = [mock_text]

        serialized = serialize_banner(mock_banner)
        self.assertEqual(serialized.id, str(mock_banner.id))
        self.assertEqual(serialized.title, "بنر مدرن")
        self.assertEqual(len(serialized.texts), 1)
        self.assertEqual(serialized.texts[0].text, "عنوان هنری")
        self.assertEqual(serialized.texts[0].position.x, 45.0)
        self.assertEqual(serialized.texts[0].position.y, 55.0)
        self.assertTrue(serialized.linkOpenInNewTab)
        self.assertTrue(serialized.isActive)

    def test_serialize_legacy_banner_fallback(self):
        """serialize_banner handles legacy documents with missing texts or fields safely."""
        from unittest.mock import MagicMock
        mock_banner = MagicMock()
        mock_banner.id = ObjectId()
        mock_banner.title = "بنر قدیمی"
        mock_banner.image = "https://example.com/old.webp"
        mock_banner.link = "/products"
        mock_banner.order = 1
        mock_banner.subtitle = "توضیحات قدیمی"
        mock_banner.badge = "ویژه"
        mock_banner.buttonText = "دیدن"
        # Legacy document has no texts, linkOpenInNewTab, isActive, timestamps
        mock_banner.texts = None
        mock_banner.linkOpenInNewTab = None
        mock_banner.isActive = None
        mock_banner.created_at = None
        mock_banner.updated_at = None

        serialized = serialize_banner(mock_banner)
        self.assertEqual(serialized.title, "بنر قدیمی")
        self.assertEqual(serialized.texts, [])
        self.assertTrue(serialized.isActive)
        self.assertFalse(serialized.linkOpenInNewTab)
        self.assertEqual(serialized.subtitle, "توضیحات قدیمی")


if __name__ == "__main__":
    unittest.main()
