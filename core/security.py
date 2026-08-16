"""Security utilities for production-grade authentication and authorization.

Authentication Architecture:
  - Access Token: Short-lived (15 min) JWT stored in client application memory.
    Sent via `Authorization: Bearer <token>` header.
  - Refresh Token: High-entropy opaque string stored only as SHA-256 hash in DB.
    Delivered via HttpOnly, Secure, SameSite cookie scoped to `/api/v1/auth`.
  - CSRF Token: Non-httpOnly cookie + `X-CSRF-Token` header for double-submit
    validation on state-changing requests.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from beanie import PydanticObjectId
from models.user import User

from core.config import settings

ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "x-csrf-token"
REFRESH_COOKIE_PATH = "/api/v1/auth"


# ─── Token Generation & Hashing ───────────────────────────────────────────────


def create_access_token(
    user_id: str,
    session_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create short-lived JWT access token with minimal essential claims."""
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": uuid.uuid4().hex,
    }
    if session_id:
        payload["session_id"] = str(session_id)

    encoded_jwt = jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def generate_refresh_token() -> str:
    """Generate a cryptographically secure, high-entropy random refresh token."""
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    """Compute SHA-256 hash of token for secure database storage and lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    """Generate a random, unguessable CSRF token."""
    return secrets.token_urlsafe(32)


# ─── Token Verification ───────────────────────────────────────────────────────


def verify_token(token: str, expected_type: Optional[str] = "access") -> dict:
    """Verify and decode a JWT, enforcing allowed algorithms and token type."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=settings.ALLOWED_ALGORITHMS,
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اعتبار سنجی توکن ناموفق بود یا منقضی شده است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if expected_type and payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نوع توکن نامعتبر است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def _extract_access_token(request: Request) -> Optional[str]:
    """Extract access token prioritizing Authorization header over cookie fallback."""
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    # Fallback to cookie for browser transitions
    cookie_token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if cookie_token:
        return cookie_token

    return None


# ─── Current-User Dependencies ───────────────────────────────────────────────


async def get_current_user(request: Request) -> User:
    """Extract and validate current authenticated user from request."""
    token = _extract_access_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="احراز هویت انجام نشده است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token, expected_type="access")
    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="شناسه کاربر در توکن نامعتبر است",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        user = await User.find_one(User.id == user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="کاربر یافت نشد",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری شما غیرفعال شده است",
        )

    return user


async def get_optional_user(request: Request) -> Optional[User]:
    """Return authenticated user or None if no valid token is provided."""
    token = _extract_access_token(request)
    if not token:
        return None
    try:
        payload = verify_token(token, expected_type="access")
        user_id: str = payload.get("sub")
        if not user_id:
            return None
        user = await User.get(PydanticObjectId(user_id))
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Validate current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری غیرفعال است",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Validate current user is a superuser."""
    if not (current_user.is_superuser or current_user.is_super_admin_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="سطح دسترسی لازم برای این عملیات را ندارید",
        )
    return current_user


# ─── Cookie Helpers ──────────────────────────────────────────────────────────


def set_auth_cookies(
    response: Response,
    refresh_token: str,
    csrf_token: Optional[str] = None,
    access_token: Optional[str] = None,
) -> None:
    """Set secure HttpOnly refresh token cookie and CSRF cookie."""
    common = dict(
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.cookie_domain,
    )

    # Scoped to /api/v1/auth so refresh token is only sent to auth routes
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        path=REFRESH_COOKIE_PATH,
        **common,
    )

    # Double-submit CSRF cookie (non-httpOnly so JS client can read and echo in header)
    if csrf_token:
        response.set_cookie(
            key=CSRF_COOKIE,
            value=csrf_token,
            max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            httponly=False,
            path="/",
            **common,
        )

    # Optional access token cookie fallback
    if access_token:
        response.set_cookie(
            key=ACCESS_TOKEN_COOKIE,
            value=access_token,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True,
            path="/",
            **common,
        )


def clear_auth_cookies(response: Response) -> None:
    """Delete all auth and CSRF cookies across all candidate paths."""
    common = dict(
        domain=settings.cookie_domain,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    # Refresh token paths (current + legacy paths)
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path=REFRESH_COOKIE_PATH, **common)
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path="/api/v1/users", **common)
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path="/", **common)

    # Access token and CSRF
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/", **common)
    response.delete_cookie(key=CSRF_COOKIE, path="/", **common)


def verify_csrf(request: Request) -> None:
    """Double-submit CSRF check for state-changing cookie requests."""
    csrf_cookie = request.cookies.get(CSRF_COOKIE)
    if not csrf_cookie:
        return

    csrf_header = request.headers.get(CSRF_HEADER)
    if not csrf_header or not secrets.compare_digest(csrf_header, csrf_cookie):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="توکن CSRF نامعتبر یا یافت نشد",
        )
