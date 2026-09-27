"""Unit tests for Order Tracking logic and schemas."""

import sys
from pathlib import Path
import unittest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from api.v1.orders import normalize_tracking_id, DEMO_TRACKING_ORDERS
from schemas.order import OrderTrackingResponse, TrackingStep


class TestOrderTrackingUnit(unittest.TestCase):
    """Unit tests for Order Tracking normalizer, demo orders, and schemas."""

    def test_normalize_tracking_id(self):
        """Test normalization of various order ID formats."""
        # Standard ASCII
        self.assertEqual(normalize_tracking_id("ORD-10042"), "ORD-10042")
        self.assertEqual(normalize_tracking_id("ord-10042"), "ORD-10042")
        self.assertEqual(normalize_tracking_id("10042"), "ORD-10042")
        self.assertEqual(normalize_tracking_id("ORD10042"), "ORD-10042")
        self.assertEqual(normalize_tracking_id("#ORD-10042"), "ORD-10042")
        self.assertEqual(normalize_tracking_id("  ORD-10042  "), "ORD-10042")

        # Persian digits
        self.assertEqual(normalize_tracking_id("۱۰۴۲"), "ORD-1042")
        self.assertEqual(normalize_tracking_id("ORD-۱۰۰۴۲"), "ORD-10042")
        self.assertEqual(normalize_tracking_id("ord-۱۰۰۴۲"), "ORD-10042")

    def test_demo_orders_schema_validation(self):
        """Verify that pre-configured demo orders pass OrderTrackingResponse validation."""
        self.assertIn("ORD-10042", DEMO_TRACKING_ORDERS)
        self.assertIn("ORD-10038", DEMO_TRACKING_ORDERS)

        for code, data in DEMO_TRACKING_ORDERS.items():
            validated = OrderTrackingResponse(**data)
            self.assertEqual(validated.orderId, code)
            self.assertTrue(len(validated.steps) >= 4)
            self.assertIsNotNone(validated.items)
            self.assertIsNotNone(validated.shippingAddress)

    def test_tracking_step_schema(self):
        """Test TrackingStep model validation."""
        step = TrackingStep(
            title="statusReceived",
            desc="سفارش ثبت گردید",
            completed=True,
        )
        self.assertEqual(step.title, "statusReceived")
        self.assertTrue(step.completed)


if __name__ == "__main__":
    unittest.main()
