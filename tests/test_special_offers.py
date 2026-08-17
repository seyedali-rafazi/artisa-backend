"""Comprehensive unit and lifecycle tests for Scheduled Special Offers and Asia/Tehran timezone handling."""

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core.timezone import (
    get_tehran_timezone,
    now_utc,
    now_tehran,
    to_utc,
    to_tehran,
    format_tehran_iso,
    get_offer_status,
    TEHRAN_TZ,
)
from models.special_offer import SpecialOffer
from schemas.special_offer import (
    SpecialOfferCreate,
    SpecialOfferUpdate,
    SpecialOfferResponse,
    SpecialOfferProductSummary,
)
from services.special_offer_service import SpecialOfferService


class TestTehranTimezoneHandling(unittest.TestCase):
    """Test suite for Asia/Tehran IANA timezone conversions and precision."""

    def test_tehran_timezone_object(self):
        """Ensure Asia/Tehran timezone is loaded properly."""
        tz = get_tehran_timezone()
        self.assertIsNotNone(tz)
        self.assertIn("Tehran", str(tz))

    def test_to_utc_with_timezone_aware_datetime(self):
        """Test converting aware datetime to UTC."""
        tehran = get_tehran_timezone()
        dt_tehran = datetime(2026, 8, 20, 18, 0, 0, tzinfo=tehran)
        dt_utc = to_utc(dt_tehran)
        
        self.assertEqual(dt_utc.tzinfo, timezone.utc)
        self.assertEqual(dt_utc, dt_tehran.astimezone(timezone.utc))
        # 18:00 Tehran with +04:30 or +03:30 offset converts precisely
        back_tehran = to_tehran(dt_utc)
        self.assertEqual(back_tehran.hour, 18)
        self.assertEqual(back_tehran.minute, 0)

    def test_to_utc_with_naive_datetime(self):
        """Naive datetimes must be interpreted as Asia/Tehran local time."""
        naive_dt = datetime(2026, 8, 20, 15, 30, 0)
        dt_utc = to_utc(naive_dt)
        self.assertEqual(dt_utc.tzinfo, timezone.utc)
        
        # When converted back to Tehran, it should match the original local time
        back_to_tehran = to_tehran(dt_utc)
        self.assertEqual(back_to_tehran.year, 2026)
        self.assertEqual(back_to_tehran.month, 8)
        self.assertEqual(back_to_tehran.day, 20)
        self.assertEqual(back_to_tehran.hour, 15)
        self.assertEqual(back_to_tehran.minute, 30)

    def test_to_utc_with_iso_string(self):
        """ISO strings with and without Z or offsets."""
        iso_utc = "2026-08-20T12:00:00Z"
        dt = to_utc(iso_utc)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.tzinfo, timezone.utc)

        iso_offset = "2026-08-20T15:30:00+03:30"
        dt_from_offset = to_utc(iso_offset)
        self.assertEqual(dt_from_offset.hour, 12)
        self.assertEqual(dt_from_offset.minute, 0)


class TestSpecialOfferLifecycleStatus(unittest.TestCase):
    """Test dynamic offer status calculation and boundary cases."""

    def test_upcoming_offer(self):
        """Offer whose start_at is in the future."""
        curr = datetime(2026, 8, 17, 12, 0, 0, tzinfo=timezone.utc)
        start = datetime(2026, 8, 18, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 8, 20, 0, 0, 0, tzinfo=timezone.utc)

        status = get_offer_status(start, end, is_active=True, reference_time=curr)
        self.assertEqual(status, "upcoming")

    def test_active_offer(self):
        """Offer currently within start_at and end_at."""
        curr = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
        start = datetime(2026, 8, 18, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 8, 20, 0, 0, 0, tzinfo=timezone.utc)

        status = get_offer_status(start, end, is_active=True, reference_time=curr)
        self.assertEqual(status, "active")

    def test_expired_offer(self):
        """Offer whose end_at is in the past."""
        curr = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)
        start = datetime(2026, 8, 18, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 8, 20, 0, 0, 0, tzinfo=timezone.utc)

        status = get_offer_status(start, end, is_active=True, reference_time=curr)
        self.assertEqual(status, "expired")

    def test_inactive_toggle_overrides_schedule(self):
        """When is_active=False, status must be inactive regardless of dates."""
        curr = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
        start = datetime(2026, 8, 18, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 8, 20, 0, 0, 0, tzinfo=timezone.utc)

        status = get_offer_status(start, end, is_active=False, reference_time=curr)
        self.assertEqual(status, "inactive")

    def test_exact_boundary_start(self):
        """Exact start_at timestamp must be considered active (start_at <= now)."""
        exact_start = datetime(2026, 8, 18, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)

        status = get_offer_status(exact_start, end, is_active=True, reference_time=exact_start)
        self.assertEqual(status, "active")

    def test_exact_boundary_end(self):
        """Exact end_at timestamp must be considered expired (now >= end_at)."""
        start = datetime(2026, 8, 18, 10, 0, 0, tzinfo=timezone.utc)
        exact_end = datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)

        status = get_offer_status(start, exact_end, is_active=True, reference_time=exact_end)
        self.assertEqual(status, "expired")


class TestSpecialOfferSchemasValidation(unittest.TestCase):
    """Test validation rules on Pydantic schemas."""

    def test_valid_offer_creation_schema(self):
        """Valid offer payload should normalize dates to UTC."""
        payload = SpecialOfferCreate(
            title="تخفیف شگفت‌انگیز پاییزه",
            description="توضیحات تست",
            product_ids=["6581f1234567890123456789", "6581f1234567890123456780"],
            start_at=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc),
            is_active=True,
        )
        self.assertEqual(payload.title, "تخفیف شگفت‌انگیز پاییزه")
        self.assertEqual(len(payload.product_ids), 2)
        self.assertEqual(payload.start_at.tzinfo, timezone.utc)
        self.assertEqual(payload.end_at.tzinfo, timezone.utc)

    def test_reject_end_at_before_start_at(self):
        """Validation must reject end_at <= start_at."""
        with self.assertRaises(ValidationError) as ctx:
            SpecialOfferCreate(
                title="تخفیف نامعتبر",
                product_ids=["6581f1234567890123456789"],
                start_at=datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc),
            )
        self.assertIn("زمان پایان پیشنهاد باید بعد از زمان شروع باشد", str(ctx.exception))

    def test_reject_equal_start_and_end(self):
        """Validation must reject end_at == start_at."""
        same_time = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
        with self.assertRaises(ValidationError) as ctx:
            SpecialOfferCreate(
                title="تخفیف نامعتبر",
                product_ids=["6581f1234567890123456789"],
                start_at=same_time,
                end_at=same_time,
            )
        self.assertIn("زمان پایان پیشنهاد باید بعد از زمان شروع باشد", str(ctx.exception))

    def test_duplicate_product_ids_deduplication(self):
        """Product IDs must be automatically deduplicated preserving order."""
        pid1 = "6581f1234567890123456789"
        pid2 = "6581f1234567890123456780"
        payload = SpecialOfferCreate(
            title="پیشنهاد با موارد تکراری",
            product_ids=[pid1, pid2, pid1, pid2, f"  {pid1}  "],
            start_at=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(payload.product_ids, [pid1, pid2])

    def test_empty_product_ids_rejection(self):
        """Empty product list must be rejected."""
        with self.assertRaises(ValidationError):
            SpecialOfferCreate(
                title="پیشنهاد بدون محصول",
                product_ids=[],
                start_at=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc),
            )

    def test_short_title_rejection(self):
        """Title shorter than 2 chars must be rejected."""
        with self.assertRaises(ValidationError):
            SpecialOfferCreate(
                title=" ",
                product_ids=["6581f1234567890123456789"],
                start_at=datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc),
                end_at=datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc),
            )


class TestSpecialOfferServiceLogic(unittest.IsolatedAsyncioTestCase):
    """Test SpecialOfferService validation and query construction."""

    async def test_validate_products_exist_missing(self):
        """Service should raise 400 when referenced products do not exist."""
        with patch.object(SpecialOfferService, "_fetch_and_map_products", new=AsyncMock(return_value={})):
            with self.assertRaises(Exception) as ctx:
                await SpecialOfferService._validate_products_exist(["invalid_pid_1", "invalid_pid_2"])
            self.assertIn("برخی از محصولات انتخاب شده یافت نشدند", str(ctx.exception))

    async def test_validate_products_exist_success(self):
        """Service should accept when all product IDs are found."""
        p_mock = SpecialOfferProductSummary(
            id="pid_123",
            name="تابلو نقاشی",
            price=1500000,
            image="/img.jpg",
            category="تابلو",
        )
        with patch.object(SpecialOfferService, "_fetch_and_map_products", new=AsyncMock(return_value={"pid_123": p_mock})):
            result = await SpecialOfferService._validate_products_exist(["pid_123"])
            self.assertEqual(result, ["pid_123"])


if __name__ == "__main__":
    unittest.main()
