"""Authentication Router with Short-Lived Access Tokens, Secure Refresh Tokens, and Session Management."""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from core.config import settings
from core.security import (
    generate_csrf_token,
    set_auth_cookies,
    clear_auth_cookies,
    get_current_user,
    verify_csrf,
    REFRESH_TOKEN_COOKIE,
)
from core.rate_limiter import (
    login_rate_limiter,
    refresh_rate_limiter,
    auth_general_rate_limiter,
)
from models.user import User
from schemas.response import success_response, error_response
from services.auth_service import AuthService
from services.audit_service import AuditLogService
from schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenRefreshPayload,
    GoogleAuthRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    VerifyResetCodeRequest,
    ResetPasswordRequest,
    AuthSessionResponse,
)

router = APIRouter()


def build_user_response(user: User) -> dict:
    """Helper to convert User model to UserResponse dict."""
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        avatar=user.avatar,
        provider=user.provider,
        email_verified=user.email_verified,
        is_verified=user.is_verified,
        createdAt=user.created_at.strftime("%Y/%m/%d") if user.created_at else None,
    ).model_dump()


@router.post(
    "/register",
    summary="Register a new user (Unverified)",
    dependencies=[Depends(auth_general_rate_limiter)],
)
async def register(payload: UserRegister, request: Request, response: Response):
    """Register a new account and send 4-digit email verification code."""
    res = await AuthService.register_user(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        phone=payload.phone,
    )
    return success_response(
        data=res,
        message=res["message"],
        status_code=status.HTTP_201_CREATED,
        response=response,
    )


@router.post(
    "/verify-email",
    summary="Verify email with 4-digit OTP",
    dependencies=[Depends(auth_general_rate_limiter)],
)
async def verify_email(
    response: Response, request: Request, payload: VerifyEmailRequest
):
    """Verify user's 4-digit code and activate account with authenticated session."""
    res = await AuthService.verify_email(
        response=response, email=payload.email, code=payload.code, request=request
    )
    user_data = build_user_response(res["user"])
    return success_response(
        data={
            "access_token": res["access_token"],
            "token_type": "bearer",
            "expires_in": res["expires_in"],
            "user": user_data,
        },
        message=res["message"],
    )


@router.post(
    "/resend-verification",
    summary="Resend verification 4-digit OTP code",
    dependencies=[Depends(auth_general_rate_limiter)],
)
async def resend_verification(payload: ResendVerificationRequest):
    """Resend verification code (max once per 60 seconds)."""
    res = await AuthService.resend_verification(email=payload.email)
    return success_response(message=res["message"])


@router.post(
    "/login",
    summary="User login",
    dependencies=[Depends(login_rate_limiter)],
)
async def login(response: Response, request: Request, payload: UserLogin):
    """Authenticate user with email and password, establishing an HttpOnly refresh token session."""
    res = await AuthService.login_user(
        response=response,
        email=payload.email,
        password=payload.password,
        request=request,
    )
    user_data = build_user_response(res["user"])
    return success_response(
        data={
            "access_token": res["access_token"],
            "token_type": "bearer",
            "expires_in": res["expires_in"],
            "user": user_data,
        },
        message=res["message"],
    )


@router.post(
    "/google",
    summary="Authenticate with Google",
    dependencies=[Depends(login_rate_limiter)],
)
async def google_auth(
    response: Response, request: Request, payload: GoogleAuthRequest
):
    """Authenticate or register user using Google OAuth ID token."""
    client_id = settings.GOOGLE_CLIENT_ID
    if not client_id:
        return error_response(
            message="تنظیمات Google Client ID روی سرور پیکربندی نشده است",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        id_info = id_token.verify_oauth2_token(
            payload.credential, google_requests.Request(), client_id
        )
        if id_info.get("iss") not in [
            "accounts.google.com",
            "https://accounts.google.com",
        ]:
            return error_response(
                message="صادرکننده توکن گوگلی نامعتبر است",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
    except ValueError as err:
        return error_response(
            message=f"توکن گوگلی نامعتبر یا منقضی شده است: {str(err)}",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    except Exception:
        return error_response(
            message="اعتبارسنجی توکن گوگلی با خطا مواجه شد",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    google_id = id_info.get("sub")
    email = id_info.get("email")
    name = id_info.get("name") or (email.split("@")[0] if email else "کاربر گوگلی")
    picture = id_info.get("picture")
    email_verified = bool(id_info.get("email_verified", False))

    if not email or not google_id:
        return error_response(
            message="اطلاعات حساب گوگل کامل نیست (ایمیل یا شناسه کاربری یافت نشد)",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = await User.find_one(User.google_id == google_id)
    if not user:
        user = await User.find_one(User.email == email)

    if user:
        user.google_id = google_id
        user.provider = "google"
        if picture:
            user.avatar = picture
        user.email_verified = email_verified or user.email_verified
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        await user.save()
    else:
        user = User(
            name=name,
            email=email,
            hashed_password=None,
            google_id=google_id,
            provider="google",
            avatar=picture,
            email_verified=email_verified,
            is_verified=True,
            role="user",
        )
        await user.insert()

    if not user.is_active:
        return error_response(
            message="حساب کاربری شما غیرفعال شده است",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    access_token, refresh_token, session = await AuthService.create_session(
        user, request=request
    )
    csrf_token = generate_csrf_token()
    set_auth_cookies(
        response,
        refresh_token=refresh_token,
        csrf_token=csrf_token,
    )

    await AuditLogService.log_action(
        user=user,
        action="GOOGLE_LOGIN_SUCCESS",
        resource="user",
        details={"session_id": str(session.id)},
        request=request,
    )

    user_data = build_user_response(user)
    return success_response(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user_data,
        },
        message="ورود با گوگل با موفقیت انجام شد",
    )


@router.post(
    "/refresh",
    summary="Refresh access token with rotation and reuse detection",
    dependencies=[Depends(refresh_rate_limiter)],
)
async def refresh_token(
    response: Response,
    request: Request,
    payload: Optional[TokenRefreshPayload] = None,
):
    """Issue a new short-lived access token and rotate the refresh token.

    Security guarantees:
    - Opaque refresh token validated from HttpOnly cookie (or JSON body fallback for non-browser clients).
    - If reuse of a revoked token is detected, all sessions in the token family are revoked.
    - Old refresh token is invalidated immediately and replaced with a new one.
    - New access token is returned in JSON; new refresh token is set in HttpOnly cookie.
    """
    token_str = request.cookies.get(REFRESH_TOKEN_COOKIE) or (
        payload.refresh_token if payload else None
    )
    if not token_str:
        return error_response(
            message="توکن بازنشانی یافت نشد",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    new_access_token, new_refresh_token, session = (
        await AuthService.rotate_refresh_token(token_str, request=request)
    )

    csrf_token = generate_csrf_token()
    set_auth_cookies(
        response,
        refresh_token=new_refresh_token,
        csrf_token=csrf_token,
    )

    return success_response(
        data={
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
        message="توکن با موفقیت تمدید شد",
    )


@router.post("/logout", summary="User logout (Current session)")
async def logout(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Revoke the current session and clear auth cookies."""
    token_str = request.cookies.get(REFRESH_TOKEN_COOKIE)
    if token_str:
        await AuthService.revoke_session_by_token(token_str)

    clear_auth_cookies(response)

    await AuditLogService.log_action(
        user=current_user,
        action="LOGOUT",
        resource="auth_session",
        request=request,
    )

    return success_response(message="از حساب کاربری خارج شدید")


@router.post("/logout-all", summary="Revoke all active sessions (Logout everywhere)")
async def logout_all(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Revoke all active sessions across all devices for the current user."""
    await AuthService.revoke_all_user_sessions(str(current_user.id))
    clear_auth_cookies(response)

    await AuditLogService.log_action(
        user=current_user,
        action="LOGOUT_ALL_SESSIONS",
        resource="auth_session",
        details={"user_id": str(current_user.id)},
        request=request,
    )

    return success_response(message="از تمام نشست‌ها و دستگاه‌ها خارج شدید")


@router.get("/sessions", summary="List active sessions for current user")
async def list_sessions(
    request: Request, current_user: User = Depends(get_current_user)
):
    """Return all active, non-expired sessions belonging to the current user."""
    token_str = request.cookies.get(REFRESH_TOKEN_COOKIE)
    sessions = await AuthService.get_user_sessions(
        str(current_user.id), current_token=token_str
    )
    return success_response(
        data=sessions,
        message="لیست نشست‌های فعال دریافت شد",
    )


@router.delete("/sessions/{session_id}", summary="Revoke a specific session")
async def revoke_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Revoke a specific active session by its ID."""
    revoked = await AuthService.revoke_session_by_id(
        session_id=session_id, user_id=str(current_user.id)
    )
    if not revoked:
        return error_response(
            message="نشست مورد نظر یافت نشد یا دسترسی لغو آن را ندارید",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    await AuditLogService.log_action(
        user=current_user,
        action="REVOKE_SESSION",
        resource="auth_session",
        details={"revoked_session_id": session_id},
        request=request,
    )

    return success_response(message="نشست مورد نظر با موفقیت لغو شد")


@router.get("/me", summary="Get authenticated user profile")
async def get_me(current_user: User = Depends(get_current_user)):
    """Fetch current user profile data."""
    user_data = build_user_response(current_user)
    return success_response(data=user_data, message="اطلاعات کاربر با موفقیت دریافت شد")


@router.post(
    "/forgot-password",
    summary="Request password reset 4-digit code",
    dependencies=[Depends(auth_general_rate_limiter)],
)
async def forgot_password(payload: ForgotPasswordRequest):
    """Send a password reset 4-digit code to user's email."""
    res = await AuthService.forgot_password(email=payload.email)
    return success_response(message=res["message"])


@router.post(
    "/verify-reset-code",
    summary="Verify password reset 4-digit code",
    dependencies=[Depends(auth_general_rate_limiter)],
)
async def verify_reset_code(payload: VerifyResetCodeRequest):
    """Validate user's password reset code."""
    res = await AuthService.verify_reset_code(
        email=payload.email, code=payload.code
    )
    return success_response(data={"valid": True}, message=res["message"])


@router.post(
    "/reset-password",
    summary="Reset password using 4-digit code",
    dependencies=[Depends(auth_general_rate_limiter)],
)
async def reset_password(
    payload: ResetPasswordRequest, request: Request
):
    """Update password using verified 4-digit code and terminate other active sessions."""
    res = await AuthService.reset_password(
        email=payload.email,
        code=payload.code,
        new_password=payload.new_password,
        request=request,
    )
    return success_response(message=res["message"])
