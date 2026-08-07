"""Permission dependencies for Role-Based Access Control (RBAC)."""

from fastapi import Depends, HTTPException, status
from models.user import User, RoleEnum
from core.security import get_current_user


async def get_active_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Validate that the current user account is active and email verified."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب کاربری شما غیرفعال شده است.",
        )

    # Allow email verification if is_verified or email_verified is true, or if local bypass
    if not (current_user.is_verified or current_user.email_verified):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="آدرس ایمیل شما تایید نشده است. لطفاً ابتدا ایمیل خود را تایید کنید.",
        )

    return current_user


async def require_admin(current_user: User = Depends(get_active_verified_user)) -> User:
    """Require user to have ADMIN or SUPER_ADMIN role."""
    if not current_user.is_admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما دسترسی لازم برای ورود به بخش مدیریت را ندارید.",
        )
    return current_user


async def require_super_admin(current_user: User = Depends(get_active_verified_user)) -> User:
    """Require user to have SUPER_ADMIN role."""
    if not current_user.is_super_admin_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="این عملیات نیازمند سطح دسترسی مدیر ارشد (Super Admin) می‌باشند.",
        )
    return current_user
