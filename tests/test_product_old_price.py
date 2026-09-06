"""Unit tests for product oldPrice handling and sanitization."""

import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from schemas.admin import ProductUpdateRequest
from services.admin_service import AdminService
from models.product import Product
from models.user import User


class TestProductOldPriceSanitization(unittest.IsolatedAsyncioTestCase):
    """Test suite for oldPrice sanitization and schema behavior."""

    def test_schema_allows_none_and_positive_old_price(self):
        """Ensure schemas accept None, 0, or positive float."""
        update_none = ProductUpdateRequest(oldPrice=None)
        self.assertIsNone(update_none.oldPrice)

        update_zero = ProductUpdateRequest(oldPrice=0)
        self.assertEqual(update_zero.oldPrice, 0.0)

        update_pos = ProductUpdateRequest(oldPrice=2000000)
        self.assertEqual(update_pos.oldPrice, 2000000.0)

    @patch("services.admin_service.AuditLogService.log_action", new_callable=AsyncMock)
    @patch("services.image_upload.cleanup_replaced_urls", new_callable=AsyncMock)
    @patch.object(Product, "get")
    async def test_update_product_clears_zero_old_price(self, mock_get, mock_cleanup, mock_log):
        """When oldPrice <= 0 or None, update_product sets product.oldPrice to None."""
        mock_product = MagicMock()
        mock_product.id = "6a77580f13cad32a838d9c3a"
        mock_product.image = "http://example.com/img.jpg"
        mock_product.gallery = []
        mock_product.price = 1000000.0
        mock_product.oldPrice = 2000000.0
        mock_product.save = AsyncMock()
        mock_get.return_value = mock_product

        mock_user = MagicMock(spec=User)
        mock_user.id = "user1"
        mock_user.role = "super_admin"

        mock_request = MagicMock()

        # Test setting oldPrice = 0
        payload_zero = ProductUpdateRequest(oldPrice=0)
        updated = await AdminService.update_product(
            admin_user=mock_user,
            product_id="6a77580f13cad32a838d9c3a",
            payload=payload_zero,
            request=mock_request,
        )

        self.assertIsNone(updated.oldPrice)
        self.assertTrue(mock_product.save.called)

        # Test setting oldPrice = None
        mock_product.oldPrice = 2000000.0
        payload_none = ProductUpdateRequest(oldPrice=None)
        updated2 = await AdminService.update_product(
            admin_user=mock_user,
            product_id="6a77580f13cad32a838d9c3a",
            payload=payload_none,
            request=mock_request,
        )
        self.assertIsNone(updated2.oldPrice)

        # Test setting valid positive oldPrice
        payload_valid = ProductUpdateRequest(oldPrice=2500000)
        updated3 = await AdminService.update_product(
            admin_user=mock_user,
            product_id="6a77580f13cad32a838d9c3a",
            payload=payload_valid,
            request=mock_request,
        )
        self.assertEqual(updated3.oldPrice, 2500000.0)


if __name__ == "__main__":
    unittest.main()
