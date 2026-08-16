"""Unit and Security tests for Production-Grade Access & Refresh Token Authentication.

Tests cover:
1. Short-lived Access Token generation, claims, algorithm restrictions, and validation.
2. Cryptographic high-entropy Refresh Token generation and SHA-256 hashing.
3. Refresh Token Rotation (valid refresh produces new token and revokes old).
4. Refresh Token Reuse Detection (reusing a rotated/revoked token revokes entire token family).
5. Session Management (logout, logout-all, listing sessions, revoking specific session).
6. In-Memory Sliding Window Rate Limiting.
7. Double-Submit CSRF Protection.
8. Device info extraction and secure cookie headers.
"""

import sys
import time
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from bson import ObjectId

import pytest
from fastapi import HTTPException, status
from jose import jwt

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core.config import settings
from core.security import (
    create_access_token,
    generate_refresh_token,
    hash_token,
    verify_token,
    generate_csrf_token,
    verify_csrf,
    set_auth_cookies,
    clear_auth_cookies,
    REFRESH_COOKIE_PATH,
)
from core.rate_limiter import SlidingWindowRateLimiter
from models.user import User
from models.auth_session import AuthSession
from services.auth_service import AuthService
from beanie.odm.documents import DocumentSettings

# Mock document settings for unit testing Beanie models without live DB
AuthSession._document_settings = DocumentSettings.model_construct(
    name="auth_sessions",
    pymongo_collection=MagicMock(),
    use_state_management=False,
)
User._document_settings = DocumentSettings.model_construct(
    name="users",
    pymongo_collection=MagicMock(),
    use_state_management=False,
)


# ─── 1. Access Token & Cryptographic Tests ────────────────────────────────────


def test_access_token_creation_and_claims():
    """Verify access token contains sub, type, iat, exp, jti and has short lifetime."""
    user_id = str(ObjectId())
    session_id = str(ObjectId())

    token = create_access_token(user_id=user_id, session_id=session_id)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

    assert payload["sub"] == user_id
    assert payload["session_id"] == session_id
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "iat" in payload
    assert "exp" in payload

    # Verify short lifetime (15 minutes = 900 seconds)
    lifetime = payload["exp"] - payload["iat"]
    assert lifetime == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def test_access_token_algorithm_restriction():
    """Verify verify_token rejects tokens signed with disallowed algorithms or wrong keys."""
    user_id = str(ObjectId())
    # Generate token signed with wrong key
    bad_token = jwt.encode(
        {"sub": user_id, "type": "access", "exp": datetime.utcnow() + timedelta(minutes=5)},
        "attacker-fake-secret-key",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_token(bad_token, expected_type="access")
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_access_token_type_enforcement():
    """Verify access token verification rejects wrong token type."""
    token = jwt.encode(
        {"sub": "user123", "type": "refresh", "exp": datetime.utcnow() + timedelta(minutes=5)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, expected_type="access")
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "نوع توکن نامعتبر است" in exc_info.value.detail


def test_access_token_expired():
    """Verify expired access token is rejected."""
    expired_token = jwt.encode(
        {"sub": "user123", "type": "access", "exp": datetime.utcnow() - timedelta(minutes=5)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_token(expired_token, expected_type="access")
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ─── 2. Refresh Token Hashing & Entropy Tests ─────────────────────────────────


def test_refresh_token_entropy_and_hashing():
    """Verify refresh token generation produces high-entropy unguessable tokens and SHA-256 hashing."""
    token1 = generate_refresh_token()
    token2 = generate_refresh_token()

    assert len(token1) >= 64
    assert token1 != token2

    hash1 = hash_token(token1)
    hash2 = hash_token(token2)

    assert hash1 == hashlib.sha256(token1.encode("utf-8")).hexdigest()
    assert hash1 != hash2
    assert len(hash1) == 64  # SHA-256 hex length


# ─── 3. Cookie Scoping & CSRF Tests ───────────────────────────────────────────


def test_cookie_helpers_scoping():
    """Verify refresh token cookie is configured with restricted path /api/v1/auth, HttpOnly, and NO access_token cookie is set."""
    mock_response = MagicMock()

    set_auth_cookies(
        response=mock_response,
        refresh_token="test_refresh_token_value",
        csrf_token="test_csrf_token_value",
    )

    # Check set_cookie calls
    set_cookie_calls = mock_response.set_cookie.call_args_list
    cookie_keys = [c[1]["key"] for c in set_cookie_calls]

    assert "refresh_token" in cookie_keys
    assert "csrf_token" in cookie_keys
    # Access token must NEVER be set in cookies
    assert "access_token" not in cookie_keys

    # Find refresh_token call kwargs
    refresh_call = next(c for c in set_cookie_calls if c[1]["key"] == "refresh_token")
    assert refresh_call[1]["httponly"] is True
    assert refresh_call[1]["path"] == "/api/v1/auth"
    assert REFRESH_COOKIE_PATH == "/api/v1/auth"

    # Find csrf_token call kwargs
    csrf_call = next(c for c in set_cookie_calls if c[1]["key"] == "csrf_token")
    assert csrf_call[1]["httponly"] is False  # Must be readable by client JS for double submit
    assert csrf_call[1]["path"] == "/"


def test_clear_auth_cookies():
    """Verify clear_auth_cookies removes cookies across all candidate and legacy paths."""
    mock_response = MagicMock()
    clear_auth_cookies(mock_response)

    delete_cookie_calls = mock_response.delete_cookie.call_args_list
    keys_and_paths = [(c[1]["key"], c[1].get("path")) for c in delete_cookie_calls]

    assert ("refresh_token", REFRESH_COOKIE_PATH) in keys_and_paths
    assert ("refresh_token", "/api/v1/users") in keys_and_paths
    assert ("refresh_token", "/") in keys_and_paths
    assert ("access_token", "/") in keys_and_paths
    assert ("csrf_token", "/") in keys_and_paths


def test_csrf_verification():
    """Verify double-submit CSRF token matching and rejection."""
    csrf_val = generate_csrf_token()

    # Valid request
    valid_request = MagicMock()
    valid_request.cookies = {"csrf_token": csrf_val}
    valid_request.headers = {"x-csrf-token": csrf_val}
    verify_csrf(valid_request)  # Should not raise

    # Invalid request (mismatched header)
    invalid_request = MagicMock()
    invalid_request.cookies = {"csrf_token": csrf_val}
    invalid_request.headers = {"x-csrf-token": "wrong_csrf_token"}

    with pytest.raises(HTTPException) as exc_info:
        verify_csrf(invalid_request)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ─── 4. Refresh Token Rotation & Reuse Detection Tests ────────────────────────


@pytest.mark.asyncio
async def test_session_creation():
    """Verify session creation saves hashed token and returns raw tokens."""
    user = User(
        name="Test User",
        email="test@example.com",
        is_active=True,
    )
    user.id = ObjectId()

    with patch.object(AuthSession, "insert", new_callable=AsyncMock) as mock_insert:
        access_token, raw_refresh_token, session = await AuthService.create_session(user)

        assert access_token is not None
        assert raw_refresh_token is not None
        assert session.user_id == str(user.id)
        assert session.token_family_id is not None
        assert session.refresh_token_hash == hash_token(raw_refresh_token)
        assert session.is_active is True
        assert session.revoked_at is None
        mock_insert.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_token_rotation_success():
    """Verify successful token rotation invalidates the old session and issues new tokens in same family."""
    user_id = str(ObjectId())
    family_id = "family_12345"
    old_raw_token = generate_refresh_token()
    old_hash = hash_token(old_raw_token)

    old_session = AuthSession(
        user_id=user_id,
        token_family_id=family_id,
        refresh_token_hash=old_hash,
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_active=True,
    )
    old_session.id = ObjectId()

    user = User(
        name="Test User",
        email="test@example.com",
        is_active=True,
    )
    user.id = ObjectId(user_id)

    with patch.object(AuthSession, "find_one", new_callable=AsyncMock, return_value=old_session), \
         patch.object(User, "get", new_callable=AsyncMock, return_value=user), \
         patch.object(AuthSession, "save", new_callable=AsyncMock) as mock_save, \
         patch.object(AuthSession, "insert", new_callable=AsyncMock) as mock_new_insert:

        new_access_token, new_raw_refresh, new_session = await AuthService.rotate_refresh_token(old_raw_token)

        assert new_access_token is not None
        assert new_raw_refresh != old_raw_token
        assert new_session.token_family_id == family_id  # Preserves family
        assert old_session.is_active is False
        assert old_session.revoked_at is not None
        assert old_session.replaced_by == str(new_session.id)
        mock_save.assert_called_once()
        mock_new_insert.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_token_reuse_detection():
    """Verify that reusing an already revoked/rotated token revokes the ENTIRE token family."""
    user_id = str(ObjectId())
    family_id = "family_theft_target"
    compromised_raw_token = generate_refresh_token()
    compromised_hash = hash_token(compromised_raw_token)

    # Session is already revoked/rotated!
    compromised_session = AuthSession(
        user_id=user_id,
        token_family_id=family_id,
        refresh_token_hash=compromised_hash,
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_active=False,
        revoked_at=datetime.utcnow() - timedelta(minutes=10),
        replaced_by=str(ObjectId()),
    )
    compromised_session.id = ObjectId()

    mock_query_set = MagicMock()
    mock_query_set.set = AsyncMock()

    with patch.object(AuthSession, "find_one", new_callable=AsyncMock, return_value=compromised_session), \
         patch.object(AuthSession, "find", return_value=mock_query_set), \
         patch("services.audit_service.AuditLogService.log_action", new_callable=AsyncMock):

        with pytest.raises(HTTPException) as exc_info:
            await AuthService.rotate_refresh_token(compromised_raw_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "استفاده مجدد از توکن باطل‌شده" in exc_info.value.detail

        # Verify entire family was revoked in DB
        mock_query_set.set.assert_called_once()


# ─── 5. Session Revocation Tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_revoke_session_by_token():
    """Verify revoking session by raw token updates session status in DB."""
    raw_token = generate_refresh_token()
    token_hash = hash_token(raw_token)

    session = AuthSession(
        user_id=str(ObjectId()),
        token_family_id="family_1",
        refresh_token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_active=True,
    )
    session.id = ObjectId()

    with patch.object(AuthSession, "find_one", new_callable=AsyncMock, return_value=session), \
         patch.object(AuthSession, "save", new_callable=AsyncMock) as mock_save:

        await AuthService.revoke_session_by_token(raw_token)

        assert session.is_active is False
        assert session.revoked_at is not None
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_revoke_all_user_sessions():
    """Verify revoke_all_user_sessions issues bulk update for all user sessions."""
    user_id = str(ObjectId())
    mock_query_set = MagicMock()
    mock_query_set.set = AsyncMock()

    with patch.object(AuthSession, "find", return_value=mock_query_set):
        await AuthService.revoke_all_user_sessions(user_id)
        mock_query_set.set.assert_called_once()


# ─── 6. Rate Limiter Tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sliding_window_rate_limiter():
    """Verify rate limiter permits requests within limit and raises 429 when exceeded."""
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=2, prefix="test_rl")
    mock_request = MagicMock()
    mock_request.client.host = "192.168.1.100"
    mock_request.headers = {}

    # First 3 requests should pass
    await limiter(mock_request)
    await limiter(mock_request)
    await limiter(mock_request)

    # 4th request must raise 429
    with pytest.raises(HTTPException) as exc_info:
        await limiter(mock_request)
    assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Retry-After" in exc_info.value.headers


# ─── 7. Security Headers & Clean API Contract Tests ───────────────────────────


@pytest.mark.asyncio
async def test_security_headers_middleware():
    """Verify security headers are present on responses."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in response.headers.get("permissions-policy", "")


def test_auth_token_response_schema():
    """Verify TokenResponse schema contains access_token and no duplicate token field."""
    from schemas.user import TokenResponse
    schema = TokenResponse.model_json_schema()
    properties = schema.get("properties", {})
    assert "access_token" in properties
    assert "token" not in properties
    assert "token_type" in properties
    assert "expires_in" in properties
