"""Unit tests for admin products table query, filtering, sorting, and pagination."""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.admin_service import AdminService
from models.product import Product


def make_mock_product(
    id_str: str,
    name: str,
    nameEn: str = "",
    sku: str = "",
    category: str = "تابلو نقاشی",
    price: float = 100000.0,
    stock: int = 10,
    status: str = "published",
    created_at: datetime = None,
    rating: float = 5.0,
):
    p = MagicMock(spec=Product)
    p.id = id_str
    p.name = name
    p.nameEn = nameEn
    p.sku = sku
    p.category = category
    p.price = price
    p.stock_quantity = stock
    p.status = status
    p.rating = rating
    p.created_at = created_at or datetime.utcnow()
    p.updated_at = p.created_at
    p.model_dump = MagicMock(
        return_value={
            "id": id_str,
            "name": name,
            "nameEn": nameEn,
            "sku": sku,
            "category": category,
            "price": price,
            "stock_quantity": stock,
            "status": status,
            "rating": rating,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
    )
    return p


class TestAdminProductsTable(unittest.IsolatedAsyncioTestCase):
    """Test suite for AdminService.list_products."""

    def setUp(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        self.mock_products = [
            make_mock_product(
                "p1", "تابلو مینیاتور گل و مرغ", "Flower Miniature", "SKU-101", "مینیاتور", 3000000, 15, "published", now - timedelta(days=2), 4.8
            ),
            make_mock_product(
                "p2", "کاسه سفالی فیروزه‌ای", "Turquoise Bowl", "SKU-202", "سفالگری", 850000, 3, "published", now - timedelta(days=1), 4.9
            ),
            make_mock_product(
                "p3", "فرش دستباف کاشان", "Kashan Rug", "SKU-303", "فرش و گلیم", 12000000, 0, "draft", now - timedelta(days=5), 5.0
            ),
            make_mock_product(
                "p4", "گلدان میناکاری اصفهان", "Isfahan Enamel Vase", "SKU-404", "میناکاری", 1500000, 8, "archived", now, 4.5
            ),
        ]

    @patch.object(Product, "all")
    async def test_list_products_default_sorts_newest_first(self, mock_all):
        mock_all.return_value.to_list = AsyncMock(return_value=list(self.mock_products))
        result = await AdminService.list_products(page=1, limit=10)

        self.assertEqual(result["total"], 4)
        self.assertEqual(len(result["items"]), 4)
        # Newest is p4 (now), followed by p2 (-1d), p1 (-2d), p3 (-5d)
        self.assertEqual(result["items"][0]["id"], "p4")
        self.assertEqual(result["items"][1]["id"], "p2")
        self.assertEqual(result["items"][2]["id"], "p1")
        self.assertEqual(result["items"][3]["id"], "p3")

    @patch.object(Product, "all")
    async def test_list_products_search_by_sku(self, mock_all):
        mock_all.return_value.to_list = AsyncMock(return_value=list(self.mock_products))
        result = await AdminService.list_products(search="SKU-202")

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], "p2")

    @patch.object(Product, "all")
    async def test_list_products_filter_status(self, mock_all):
        mock_all.return_value.to_list = AsyncMock(return_value=list(self.mock_products))
        result = await AdminService.list_products(status_filter="published")

        self.assertEqual(result["total"], 2)
        ids = [item["id"] for item in result["items"]]
        self.assertIn("p1", ids)
        self.assertIn("p2", ids)

    @patch.object(Product, "all")
    async def test_list_products_filter_category(self, mock_all):
        mock_all.return_value.to_list = AsyncMock(return_value=list(self.mock_products))
        result = await AdminService.list_products(category="میناکاری")

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], "p4")

    @patch.object(Product, "all")
    async def test_list_products_sort_by_price_desc(self, mock_all):
        mock_all.return_value.to_list = AsyncMock(return_value=list(self.mock_products))
        result = await AdminService.list_products(sort_by="price", sort_order="desc")

        prices = [item["price"] for item in result["items"]]
        self.assertEqual(prices, [12000000, 3000000, 1500000, 850000])

    @patch.object(Product, "all")
    async def test_list_products_sort_by_price_asc(self, mock_all):
        mock_all.return_value.to_list = AsyncMock(return_value=list(self.mock_products))
        result = await AdminService.list_products(sort_by="price", sort_order="asc")

        prices = [item["price"] for item in result["items"]]
        self.assertEqual(prices, [850000, 1500000, 3000000, 12000000])

    @patch.object(Product, "all")
    async def test_list_products_pagination(self, mock_all):
        mock_all.return_value.to_list = AsyncMock(return_value=list(self.mock_products))
        result = await AdminService.list_products(page=1, limit=2)

        self.assertEqual(result["total"], 4)
        self.assertEqual(result["total_pages"], 2)
        self.assertEqual(len(result["items"]), 2)


if __name__ == "__main__":
    unittest.main()
