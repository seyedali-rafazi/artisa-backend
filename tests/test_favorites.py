"""Unit and Integration tests for Favorites API and Document Model."""

import sys
from pathlib import Path
import pytest
from bson import ObjectId

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from models.user import User
from models.product import Product
from models.favorite import Favorite
from core.security import create_access_token


@pytest.mark.asyncio
async def test_favorite_model_creation():
    """Test creating and saving a Favorite model instance."""
    user_id = str(ObjectId())
    product_id = str(ObjectId())

    fav = Favorite(user_id=user_id, product_id=product_id)
    assert fav.user_id == user_id
    assert fav.product_id == product_id
    assert fav.created_at is not None


@pytest.mark.asyncio
async def test_unauthenticated_access(async_client):
    """Ensure unauthenticated requests to favorites API return 401 Unauthorized."""
    product_id = str(ObjectId())

    # Add favorite
    res = await async_client.post(f"/api/v1/favorites/{product_id}")
    assert res.status_code == 401

    # Remove favorite
    res = await async_client.delete(f"/api/v1/favorites/{product_id}")
    assert res.status_code == 401

    # List favorites
    res = await async_client.get("/api/v1/favorites")
    assert res.status_code == 401

    # Get favorite IDs
    res = await async_client.get("/api/v1/favorites/ids")
    assert res.status_code == 401

    # Get favorite status
    res = await async_client.get(f"/api/v1/favorites/{product_id}/status")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_favorites_crud_and_isolation(async_client):
    """Test full favorite workflow: add, status check, get list, remove, and multi-user isolation."""
    # 1. Create two test users in database
    user1 = User(
        name="User One",
        email=f"user1_{ObjectId()}@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
    )
    await user1.insert()
    token1 = create_access_token(data={"sub": str(user1.id)})
    headers1 = {"Authorization": f"Bearer {token1}"}

    user2 = User(
        name="User Two",
        email=f"user2_{ObjectId()}@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
    )
    await user2.insert()
    token2 = create_access_token(data={"sub": str(user2.id)})
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 2. Create test product in database
    product = Product(
        name="کاسه سفالی دستی",
        nameEn="Handmade Pottery Bowl",
        price=150000,
        category="سفال",
        categoryEn="pottery",
        rating=4.8,
        description="توضیحات تست",
        stock_quantity=10,
        status="published",
    )
    await product.insert()
    pid = str(product.id)

    # 3. Add to favorites for User 1
    res = await async_client.post(f"/api/v1/favorites/{pid}", headers=headers1)
    assert res.status_code in [200, 201]
    body = res.json()
    assert body["success"] is True
    assert body["data"]["is_favorited"] is True

    # 4. Check status for User 1
    res = await async_client.get(f"/api/v1/favorites/{pid}/status", headers=headers1)
    assert res.status_code == 200
    assert res.json()["data"]["is_favorited"] is True

    # 5. Check status for User 2 (Isolation check: User 2 should NOT have it favorited)
    res = await async_client.get(f"/api/v1/favorites/{pid}/status", headers=headers2)
    assert res.status_code == 200
    assert res.json()["data"]["is_favorited"] is False

    # 6. Fetch favorite IDs for User 1
    res = await async_client.get("/api/v1/favorites/ids", headers=headers1)
    assert res.status_code == 200
    assert pid in res.json()["data"]["favorite_ids"]

    # 7. Fetch favorite product list for User 1
    res = await async_client.get("/api/v1/favorites", headers=headers1)
    assert res.status_code == 200
    fav_products = res.json()["data"]
    assert len(fav_products) >= 1
    assert any(p["id"] == pid for p in fav_products)

    # 8. Duplicate favorite attempt by User 1 (should be idempotent)
    res = await async_client.post(f"/api/v1/favorites/{pid}", headers=headers1)
    assert res.status_code in [200, 201]
    assert res.json()["data"]["is_favorited"] is True

    # 9. Remove favorite for User 1
    res = await async_client.delete(f"/api/v1/favorites/{pid}", headers=headers1)
    assert res.status_code == 200
    assert res.json()["data"]["is_favorited"] is False

    # 10. Verify User 1 favorite list is now empty
    res = await async_client.get("/api/v1/favorites/ids", headers=headers1)
    assert res.status_code == 200
    assert pid not in res.json()["data"]["favorite_ids"]


@pytest.mark.asyncio
async def test_non_existent_product_favorite(async_client):
    """Test favoriting a non-existent product returns 404 Not Found."""
    user = User(
        name="Test User 404",
        email=f"user404_{ObjectId()}@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
    )
    await user.insert()
    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    fake_pid = str(ObjectId())
    res = await async_client.post(f"/api/v1/favorites/{fake_pid}", headers=headers)
    assert res.status_code == 404
    assert res.json()["success"] is False
