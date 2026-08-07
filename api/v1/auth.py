"""Authentication Router."""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from passlib.context import CryptContext
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    generate_csrf_token,
    set_auth_cookies,
    clear_auth_cookies,
    verify_token,
    get_current_user,
)
from models.user import User
from schemas.response import success_response, error_response
from services.auth_service import AuthService
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
        createdAt=user.created_at.strftime("%Y/%m/%d"),
    ).model_dump()


@router.post("/register", summary="Register a new user (Unverified)")
async def register(payload: UserRegister):
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
    )


@router.post("/verify-email", summary="Verify email with 4-digit OTP")
async def verify_email(response: Response, payload: VerifyEmailRequest):
    """Verify user's 4-digit code and activate account."""
    res = await AuthService.verify_email(
        response=response, email=payload.email, code=payload.code
    )
    user_data = build_user_response(res["user"])
    return success_response(
        data={
            "token": res["token"],
            "refresh_token": res["refresh_token"],
            "user": user_data,
        },
        message=res["message"],
    )


@router.post("/resend-verification", summary="Resend verification 4-digit OTP code")
async def resend_verification(payload: ResendVerificationRequest):
    """Resend verification code (max once per 60 seconds)."""
    res = await AuthService.resend_verification(email=payload.email)
    return success_response(message=res["message"])


@router.post("/login", summary="User login")
async def login(response: Response, payload: UserLogin):
    """Authenticate user with email and password."""
    res = await AuthService.login_user(
        response=response, email=payload.email, password=payload.password
    )
    user_data = build_user_response(res["user"])
    return success_response(
        data={
            "token": res["token"],
            "refresh_token": res["refresh_token"],
            "user": user_data,
        },
        message=res["message"],
    )


@router.post("/google", summary="Authenticate with Google")
async def google_auth(response: Response, payload: GoogleAuthRequest):
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
        if id_info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            return error_response(
                message="صادرکننده توکن گوگلی نامعتبر است",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
    except ValueError as err:
        return error_response(
            message=f"توکن گوگلی نامعتبر یا منقضی شده است: {str(err)}",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    except Exception as err:
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
            role="کاربر عادی",
        )
        await user.insert()

    if not user.is_active:
        return error_response(
            message="حساب کاربری شما غیرفعال شده است",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    csrf_token = generate_csrf_token()
    set_auth_cookies(response, access_token, refresh_token, csrf_token)

    user_data = build_user_response(user)
    return success_response(
        data={"token": access_token, "refresh_token": refresh_token, "user": user_data},
        message="ورود با گوگل با موفقیت انجام شد",
    )


@router.post("/forgot-password", summary="Request password reset 4-digit code")
async def forgot_password(payload: ForgotPasswordRequest):
    """Send a password reset 4-digit code to user's email."""
    res = await AuthService.forgot_password(email=payload.email)
    return success_response(message=res["message"])


@router.post("/verify-reset-code", summary="Verify password reset 4-digit code")
async def verify_reset_code(payload: VerifyResetCodeRequest):
    """Validate user's password reset code."""
    res = await AuthService.verify_reset_code(
        email=payload.email, code=payload.code
    )
    return success_response(data={"valid": True}, message=res["message"])


@router.post("/reset-password", summary="Reset password using 4-digit code")
async def reset_password(payload: ResetPasswordRequest):
    """Update password using verified 4-digit code."""
    res = await AuthService.reset_password(
        email=payload.email, code=payload.code, new_password=payload.new_password
    )
    return success_response(message=res["message"])


@router.post("/logout", summary="User logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Logout current user and clear auth cookies."""
    clear_auth_cookies(response)
    return success_response(message="از حساب کاربری خارج شدید")


@router.post("/refresh", summary="Refresh access token")
async def refresh_token(
    response: Response,
    request: Request,
    payload: Optional[TokenRefreshPayload] = None,
):
    """Issue new access token using refresh token."""
    token_str = (payload and payload.refresh_token) or request.cookies.get("refresh_token")
    if not token_str:
        return error_response(
            message="توکن بازنشانی یافت نشد", status_code=status.HTTP_401_UNAUTHORIZED
        )

    try:
        token_payload = verify_token(token_str, expected_type="refresh")
    except Exception:
        return error_response(
            message="توکن بازنشانی نامعتبر یا منقضی شده است", status_code=status.HTTP_401_UNAUTHORIZED
        )

    user_id = token_payload.get("sub")
    user = await User.get(user_id)
    if not user or not user.is_active:
        return error_response(
            message="کاربر غیرفعال یا یافت نشد", status_code=status.HTTP_401_UNAUTHORIZED
        )

    new_access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    new_csrf_token = generate_csrf_token()

    set_auth_cookies(response, new_access_token, new_refresh_token, new_csrf_token)

    return success_response(
        data={"token": new_access_token, "refresh_token": new_refresh_token},
        message="توکن با موفقیت تمدید شد",
    )
