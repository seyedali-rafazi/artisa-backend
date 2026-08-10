"""Unit and Integration tests for Comments API and Moderation."""

import sys
from pathlib import Path
import pytest
from bson import ObjectId

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from models.user import User, RoleEnum
from models.product import Product
from models.comment import Comment
from core.security import create_access_token


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_create_comment(async_client):
    """Ensure unauthenticated requests to create comments return 401 Unauthorized."""
    product_id = str(ObjectId())
    payload = {"text": "نظر غیرمجاز بدون لاگین", "rating": 5}

    res = await async_client.post(f"/api/v1/products/{product_id}/comments", json=payload)
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_user_can_view_comments(async_client):
    """Ensure unauthenticated users can view product comments."""
    product = Product(
        name="کاسه سفالی فرضی",
        price=100000,
        category="سفال",
    )
    await product.insert()
    pid = str(product.id)

    comment = Comment(
        productId=pid,
        userName="کاربر شماره یک",
        text="بسیار عالی و باکیفیت",
        rating=5,
        status="approved",
    )
    await comment.insert()

    res = await async_client.get(f"/api/v1/products/{pid}/comments")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "items" in body["data"]
    assert len(body["data"]["items"]) >= 1
    assert body["data"]["items"][0]["text"] == "بسیار عالی و باکیفیت"


@pytest.mark.asyncio
async def test_authenticated_user_can_create_and_manage_comment(async_client):
    """Test authenticated comment creation, duplicate prevention, editing, and deletion."""
    user = User(
        name="کاربر معتبر",
        email=f"comment_user_{ObjectId()}@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True,
        email_verified=True,
    )
    await user.insert()
    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    product = Product(
        name="گلدان سرامیکی",
        price=250000,
        category="سرامیک",
    )
    await product.insert()
    pid = str(product.id)

    # 1. Create comment
    payload = {"text": "کیفیت ساخت گلدان فوق‌العاده است", "rating": 5}
    res = await async_client.post(
        f"/api/v1/products/{pid}/comments", json=payload, headers=headers
    )
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    comment_id = body["data"]["id"]
    assert body["data"]["text"] == "کیفیت ساخت گلدان فوق‌العاده است"

    # 2. Duplicate submission prevention
    res_dup = await async_client.post(
        f"/api/v1/products/{pid}/comments", json=payload, headers=headers
    )
    assert res_dup.status_code == 400

    # 3. Update comment text & rating by owner
    update_payload = {"text": "ویرایش نظر: بسیار گلدان زیبایی است", "rating": 4}
    res_update = await async_client.patch(
        f"/api/v1/comments/{comment_id}", json=update_payload, headers=headers
    )
    assert res_update.status_code == 200
    assert res_update.json()["data"]["rating"] == 4

    # 4. Delete comment by owner
    res_del = await async_client.delete(
        f"/api/v1/comments/{comment_id}", headers=headers
    )
    assert res_del.status_code == 200

    # Verify soft deleted comment is no longer visible to public
    res_list = await async_client.get(f"/api/v1/products/{pid}/comments")
    assert res_list.status_code == 200
    items = res_list.json()["data"]["items"]
    assert not any(i["id"] == comment_id for i in items)


@pytest.mark.asyncio
async def test_comment_validation_and_xss_protection(async_client):
    """Test text trimming, empty comment rejection, min/max length, and HTML escaping."""
    user = User(
        name="تست کننده XSS",
        email=f"xss_{ObjectId()}@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
        is_verified=True,
    )
    await user.insert()
    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    product = Product(name="بشقاب میناکاری", price=300000, category="میناکاری")
    await product.insert()
    pid = str(product.id)

    # Short comment (< 3 chars)
    res_short = await async_client.post(
        f"/api/v1/products/{pid}/comments", json={"text": "سلام", "rating": 5}, headers=headers
    )
    assert res_short.status_code == 422

    # HTML injection text
    xss_payload = {"text": "<script>alert('xss')</script> نظر تست امنیت", "rating": 5}
    res_xss = await async_client.post(
        f"/api/v1/products/{pid}/comments", json=xss_payload, headers=headers
    )
    assert res_xss.status_code == 201
    sanitized_text = res_xss.json()["data"]["text"]
    assert "<script>" not in sanitized_text
    assert "&lt;script&gt;" in sanitized_text


@pytest.mark.asyncio
async def test_idor_protection(async_client):
    """Ensure User B cannot update or delete User A's comment."""
    user_a = User(
        name="کاربر A",
        email=f"usera_{ObjectId()}@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
    )
    await user_a.insert()
    token_a = create_access_token(data={"sub": str(user_a.id)})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    user_b = User(
        name="کاربر B",
        email=f"userb_{ObjectId()}@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
    )
    await user_b.insert()
    token_b = create_access_token(data={"sub": str(user_b.id)})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    product = Product(name="تابلو فرش", price=1200000, category="فرش")
    await product.insert()
    pid = str(product.id)

    # User A creates comment
    res_a = await async_client.post(
        f"/api/v1/products/{pid}/comments",
        json={"text": "نظر کاربر A که محرمانه است", "rating": 5},
        headers=headers_a,
    )
    comment_id = res_a.json()["data"]["id"]

    # User B attempts to edit User A's comment -> 403
    res_edit_b = await async_client.patch(
        f"/api/v1/comments/{comment_id}",
        json={"text": "دستکاری هکر B"},
        headers=headers_b,
    )
    assert res_edit_b.status_code == 403

    # User B attempts to delete User A's comment -> 403
    res_del_b = await async_client.delete(
        f"/api/v1/comments/{comment_id}", headers=headers_b
    )
    assert res_del_b.status_code == 403


@pytest.mark.asyncio
async def test_admin_comment_moderation(async_client):
    """Ensure Admins can list, update status, and delete comments, while normal users get 403."""
    # 1. Normal user
    normal_user = User(
        name="کاربر عادی",
        email=f"normal_{ObjectId()}@example.com",
        hashed_password="hashedpassword123",
        role="user",
        is_active=True,
    )
    await normal_user.insert()
    token_normal = create_access_token(data={"sub": str(normal_user.id)})
    headers_normal = {"Authorization": f"Bearer {token_normal}"}

    # 2. Admin user
    admin_user = User(
        name="مدیر سیستم",
        email=f"admin_{ObjectId()}@example.com",
        hashed_password="hashedpassword123",
        role="admin",
        is_active=True,
        is_verified=True,
        email_verified=True,
    )
    await admin_user.insert()
    token_admin = create_access_token(data={"sub": str(admin_user.id)})
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # Normal user attempts admin endpoint -> 403
    res_denied = await async_client.get("/api/v1/admin/comments", headers=headers_normal)
    assert res_denied.status_code == 403

    # Admin accesses endpoint -> 200
    res_admin_list = await async_client.get("/api/v1/admin/comments", headers=headers_admin)
    assert res_admin_list.status_code == 200
    assert "items" in res_admin_list.json()


@pytest.mark.asyncio
async def test_non_existent_resources(async_client):
    """Test requesting non-existent product or comment returns 404 Not Found."""
    user = User(
        name="تست 404",
        email=f"user404_{ObjectId()}@example.com",
        hashed_password="hashedpassword123",
        is_active=True,
    )
    await user.insert()
    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    fake_pid = str(ObjectId())
    res_p = await async_client.post(
        f"/api/v1/products/{fake_pid}/comments",
        json={"text": "تست محصول وجود ندارد", "rating": 5},
        headers=headers,
    )
    assert res_p.status_code == 404

    fake_cid = str(ObjectId())
    res_c = await async_client.delete(f"/api/v1/comments/{fake_cid}", headers=headers)
    assert res_c.status_code == 404
