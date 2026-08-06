"""Authentication Router."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from passlib.context import CryptContext

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
from schemas.user import UserRegister, UserLogin, UserResponse

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


@router.post("/register", summary="Register a new user")
async def register(response: Response, payload: UserRegister):
    """Register a new account."""
    existing_user = await User.find_one(User.email == payload.email)
    if existing_user:
        return error_response(
            message="کاربری با این ایمیل قبلاً ثبت نام کرده است",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        phone=payload.phone,
        role="کاربر عادی",
    )
    await user.insert()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    csrf_token = generate_csrf_token()

    set_auth_cookies(response, access_token, refresh_token, csrf_token)

    user_data = UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        createdAt=user.created_at.strftime("%Y/%m/%d"),
    ).model_dump()

    return success_response(
        data={"token": access_token, "user": user_data},
        message="ثبت نام با موفقیت انجام شد",
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/login", summary="User login")
async def login(response: Response, payload: UserLogin):
    """Authenticate user with email and password."""
    user = await User.find_one(User.email == payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        return error_response(
            message="ایمیل یا رمز عبور اشتباه است",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return error_response(
            message="حساب کاربری شما غیرفعال شده است",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    csrf_token = generate_csrf_token()

    set_auth_cookies(response, access_token, refresh_token, csrf_token)

    user_data = UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role,
        createdAt=user.created_at.strftime("%Y/%m/%d"),
    ).model_dump()

    return success_response(
        data={"token": access_token, "user": user_data},
        message="ورود با موفقیت انجام شد",
    )


@router.post("/logout", summary="User logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Logout current user and clear auth cookies."""
    clear_auth_cookies(response)
    return success_response(message="از حساب کاربری خارج شدید")


@router.post("/refresh", summary="Refresh access token")
async def refresh_token(response: Response, refresh_token: str = None):
    """Issue new access token using refresh token."""
    if not refresh_token:
        return error_response(
            message="توکن بازنشانی یافت نشد", status_code=status.HTTP_401_UNAUTHORIZED
        )

    payload = verify_token(refresh_token, expected_type="refresh")
    user_id = payload.get("sub")
    user = await User.get(user_id)
    if not user or not user.is_active:
        return error_response(
            message="کاربر غیرفعال یا یافت نشد", status_code=status.HTTP_401_UNAUTHORIZED
        )

    new_access_token = create_access_token({"sub": str(user.id)})
    new_csrf_token = generate_csrf_token()

    set_auth_cookies(response, new_access_token, refresh_token, new_csrf_token)

    return success_response(
        data={"token": new_access_token},
        message="توکن با موفقیت تمدید شد",
    )
