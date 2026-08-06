"""Security utilities for authentication and authorization.

Authentication is cookie-based:
  - `access_token`  / `refresh_token` are httpOnly cookies, so they can never
    be read by JavaScript (protects against token theft via XSS).
  - `csrf_token` is a *non*-httpOnly cookie used for the double-submit CSRF
    check on state-changing requests (see `verify_csrf`).

As a convenience for non-browser API clients (e.g. Postman/mobile), an
`Authorization: Bearer <token>` header is still accepted as a fallback when
no cookie is present. Browser requests from the frontend never need to set
this header — the cookie is sent automatically.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from models.user import User

from core.config import settings

ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "x-csrf-token"


# ─── Token creation ─────────────────────────────────────────────────────────


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def generate_csrf_token() -> str:
    """Generate a random, unguessable CSRF token."""
    return secrets.token_urlsafe(32)


def verify_token(token: str, expected_type: Optional[str] = None) -> dict:
    """Verify and decode a JWT, optionally enforcing its `type` claim.

    Enforcing `expected_type` matters: without it, a (longer-lived) refresh
    token could be replayed directly against protected endpoints as if it
    were a (short-lived) access token.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if expected_type and payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def _extract_access_token(request: Request) -> Optional[str]:
    """Read the access token from the httpOnly cookie, falling back to an
    `Authorization: Bearer` header for non-browser API clients."""
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if token:
        return token

    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:]

    return None


# ─── Current-user dependencies ──────────────────────────────────────────────


async def get_current_user(request: Request) -> User:
    """Get current authenticated user from the access-token cookie."""
    token = _extract_access_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token, expected_type="access")

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await User.get(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return user


async def get_optional_user(request: Request) -> Optional[User]:
    """Return the authenticated user or None if no valid token is present."""
    token = _extract_access_token(request)
    if not token:
        return None
    try:
        payload = verify_token(token, expected_type="access")
    except HTTPException:
        return None
    user_id: str = payload.get("sub")
    if not user_id:
        return None
    try:
        from beanie import PydanticObjectId

        user = await User.get(PydanticObjectId(user_id))
    except Exception:
        return None
    if not user or not user.is_active:
        return None
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


# ─── Cookie helpers ─────────────────────────────────────────────────────────


def set_auth_cookies(
    response: Response, access_token: str, refresh_token: str, csrf_token: str
) -> None:
    """Attach httpOnly auth cookies + a JS-readable CSRF cookie to a response."""
    common = dict(
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.cookie_domain,
    )

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        path="/",
        **common,
    )
    # Scoped to /api/v1/users so the long-lived refresh token is only ever
    # sent to the refresh/logout endpoints, not on every API call.
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        path="/api/v1/users",
        **common,
    )
    # Deliberately NOT httpOnly: the frontend reads this value and echoes it
    # back as the `X-CSRF-Token` header on state-changing requests
    # (double-submit cookie pattern). It is useless without also having a
    # valid session cookie, so exposing it to JS is safe.
    response.set_cookie(
        key=CSRF_COOKIE,
        value=csrf_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        httponly=False,
        path="/",
        **common,
    )


def clear_auth_cookies(response: Response) -> None:
    """Remove all auth cookies (used on logout)."""
    common = dict(
        domain=settings.cookie_domain,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/", **common)
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path="/api/v1/users", **common)
    response.delete_cookie(key=CSRF_COOKIE, path="/", **common)


def verify_csrf(request: Request) -> None:
    """Double-submit CSRF check for cookie-authenticated, state-changing
    requests (POST/PUT/PATCH/DELETE).

    If there is no CSRF cookie at all, the request isn't relying on an
    ambient cookie session (e.g. an anonymous guest action, or a non-browser
    client using the `Authorization` header), so there is no session to
    hijack and the check is skipped.
    """
    csrf_cookie = request.cookies.get(CSRF_COOKIE)
    if not csrf_cookie:
        return

    csrf_header = request.headers.get(CSRF_HEADER)
    if not csrf_header or not secrets.compare_digest(csrf_header, csrf_cookie):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid CSRF token",
        )


# Made with Bob
