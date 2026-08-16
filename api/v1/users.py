"""User Profile Router."""

from fastapi import APIRouter, Depends, Request, Response, status
from passlib.context import CryptContext

from core.security import get_current_user, clear_auth_cookies
from models.user import User
from schemas.response import success_response, error_response
from schemas.user import UserResponse, UserUpdate, PasswordChange
from services.auth_service import AuthService
from services.audit_service import AuditLogService

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/me", summary="Get current user profile")
async def get_me(current_user: User = Depends(get_current_user)):
    """Fetch profile of current logged in user."""
    data = UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        createdAt=current_user.created_at.strftime("%Y/%m/%d") if current_user.created_at else None,
    ).model_dump()
    return success_response(data=data, message="اطلاعات کاربر با موفقیت دریافت شد")


@router.put("/profile", summary="Update profile information")
async def update_profile(
    payload: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Update name or phone of authenticated user."""
    if payload.name is not None:
        current_user.name = payload.name
    if payload.phone is not None:
        current_user.phone = payload.phone

    await current_user.save()

    await AuditLogService.log_action(
        user=current_user,
        action="PROFILE_UPDATED",
        resource="user",
        details={"name": current_user.name, "phone": current_user.phone},
        request=request,
    )

    data = UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        createdAt=current_user.created_at.strftime("%Y/%m/%d") if current_user.created_at else None,
    ).model_dump()
    return success_response(data=data, message="اطلاعات کاربری با موفقیت ویرایش شد")


@router.put("/password", summary="Change current password")
async def change_password(
    payload: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Change password after validating current password and revoke all existing sessions."""
    if not pwd_context.verify(payload.currentPassword, current_user.hashed_password):
        return error_response(
            message="رمز عبور فعلی نادرست است",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    current_user.hashed_password = pwd_context.hash(payload.newPassword)
    await current_user.save()

    # Revoke all active sessions on password change to protect against account takeover
    await AuthService.revoke_all_user_sessions(str(current_user.id))

    await AuditLogService.log_action(
        user=current_user,
        action="PASSWORD_CHANGE_SUCCESS",
        resource="user",
        details={"user_id": str(current_user.id)},
        request=request,
    )

    return success_response(message="رمز عبور با موفقیت تغییر یافت. لطفاً مجدداً وارد شوید.")


@router.delete("/account", summary="Delete user account")
async def delete_account(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Delete current user account, revoke sessions, and clear cookies."""
    current_user.is_active = False
    await current_user.save()

    await AuthService.revoke_all_user_sessions(str(current_user.id))
    clear_auth_cookies(response)

    await AuditLogService.log_action(
        user=current_user,
        action="ACCOUNT_DELETED",
        resource="user",
        details={"user_id": str(current_user.id)},
        request=request,
    )

    return success_response(message="حساب کاربری با موفقیت حذف گردید")
