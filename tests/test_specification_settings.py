"""Unit tests for Specification Settings schemas and functionality."""

import sys
import unittest
from datetime import datetime
from pathlib import Path
from bson import ObjectId
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from schemas.specification_setting import (
    SpecificationSettingCreate,
    SpecificationSettingUpdate,
    SpecificationSettingResponse,
)
from api.v1.specification_settings import (
    serialize_setting,
    build_persian_regex,
    DEFAULT_SPECIFICATION_SEEDS,
)


class TestSpecificationSettingSchemas(unittest.TestCase):
    """Test validation and serialization of Specification Settings."""

    def test_create_validation_success(self):
        """Valid payload creates SpecificationSettingCreate successfully."""
        req = SpecificationSettingCreate(
            title="تکنیک",
            default_value="رنگ‌روغن روی بوم",
            category="تابلو نقاشی",
            description="تکنیک نقاشی",
            order=1,
            is_active=True,
        )
        self.assertEqual(req.title, "تکنیک")
        self.assertEqual(req.default_value, "رنگ‌روغن روی بوم")
        self.assertEqual(req.category, "تابلو نقاشی")
        self.assertEqual(req.order, 1)
        self.assertTrue(req.is_active)

    def test_create_validation_defaults(self):
        """Payload with only title should apply default values."""
        req = SpecificationSettingCreate(title="ابعاد")
        self.assertEqual(req.title, "ابعاد")
        self.assertEqual(req.default_value, "")
        self.assertIsNone(req.category)
        self.assertEqual(req.order, 0)
        self.assertTrue(req.is_active)

    def test_create_validation_empty_title_fails(self):
        """Empty title raises ValidationError."""
        with self.assertRaises(ValidationError):
            SpecificationSettingCreate(title="")

    def test_update_validation_partial(self):
        """Update schema allows partial updates."""
        req = SpecificationSettingUpdate(default_value="۸۰ × ۱۲۰ سانتی‌متر")
        self.assertIsNone(req.title)
        self.assertEqual(req.default_value, "۸۰ × ۱۲۰ سانتی‌متر")

    def test_serialize_setting(self):
        """serialize_setting correctly maps document to response schema."""
        from unittest.mock import MagicMock
        mock_setting = MagicMock()
        mock_setting.id = ObjectId()
        mock_setting.title = "جنس بوم"
        mock_setting.default_value = "کتان مرغوب"
        mock_setting.category = "تابلو نقاشی"
        mock_setting.description = "جنس بستر"
        mock_setting.order = 4
        mock_setting.is_active = True
        mock_setting.created_at = datetime.now()
        mock_setting.updated_at = datetime.now()

        res = serialize_setting(mock_setting)
        self.assertEqual(res.id, str(mock_setting.id))
        self.assertEqual(res.title, "جنس بوم")
        self.assertEqual(res.default_value, "کتان مرغوب")
        self.assertEqual(res.category, "تابلو نقاشی")
        self.assertEqual(res.order, 4)
        self.assertTrue(res.is_active)

    def test_build_persian_regex(self):
        """Regex helper maps Persian characters like ی and ک."""
        reg = build_persian_regex("تکنیک")
        self.assertIn("[کك]", reg)
        self.assertIn("[یي]", reg)

    def test_default_seeds_content(self):
        """Default seeds contains core art gallery presets."""
        titles = [s["title"] for s in DEFAULT_SPECIFICATION_SEEDS]
        self.assertIn("تکنیک", titles)
        self.assertIn("ابعاد", titles)
        self.assertIn("سبک", titles)
        self.assertIn("قاب", titles)


if __name__ == "__main__":
    unittest.main()
