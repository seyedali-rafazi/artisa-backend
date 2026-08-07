"""Auth Service orchestrating high-level authentication, verification, and password recovery logic."""

from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from fastapi import HTTPException, status, Response
from passlib.context import CryptContext

from core.security import (
    create_access_token,
    create_refresh_token,
    generate_csrf_token,
    set_auth_cookies,
)
from models.user import User
from services.otp_service import OTPService
from services.email_service import EmailService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service encapsulating authentication workflows."""

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
        """Verify plain password against bcrypt hash."""
        if not hashed_password:
            return False
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    async def register_user(
        cls, name: str, email: str, password: str, phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a new unverified user and send 4-digit verification code."""
        existing_user = await User.find_one(User.email == email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="کاربری با این ایمیل قبلاً ثبت نام کرده است",
            )

        hashed_pwd = cls.get_password_hash(password)
        user = User(
            name=name,
            email=email,
            hashed_password=hashed_pwd,
            phone=phone,
            is_verified=False,
            role="کاربر عادی",
            provider="local",
        )
        await user.insert()

        # Create and send verification code
        code, remaining = await OTPService.create_verification_code(
            user_id=str(user.id), email=email, code_type="email_verification"
        )
        if code:
            EmailService.send_verification_email(
                to_email=user.email, name=user.name, code=code
            )

        return {
            "user_id": str(user.id),
            "email": user.email,
            "is_verified": False,
            "message": "حساب کاربری ایجاد شد. کد تایید به ایمیل شما ارسال گردید.",
        }

    @classmethod
    async def verify_email(
        cls, response: Response, email: str, code: str
    ) -> Dict[str, Any]:
        """Verify user's email with 4-digit code and issue JWT tokens."""
        user = await User.find_one(User.email == email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="کاربری با این ایمیل یافت نشد",
            )

        if user.is_verified:
            # Already verified, generate tokens directly
            access_token = create_access_token({"sub": str(user.id)})
            refresh_token = create_refresh_token({"sub": str(user.id)})
            csrf_token = generate_csrf_token()
            set_auth_cookies(response, access_token, refresh_token, csrf_token)
            return {
                "token": access_token,
                "refresh_token": refresh_token,
                "user": user,
                "message": "حساب کاربری شما قبلاً تایید شده است",
            }

        is_valid, err_msg = await OTPService.verify_code(
            email=email, code=code, code_type="email_verification"
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg
            )

        # Mark user as verified
        user.is_verified = True
        user.email_verified = True
        user.updated_at = datetime.utcnow()
        await user.save()

        # Issue JWT tokens & set cookies
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        csrf_token = generate_csrf_token()
        set_auth_cookies(response, access_token, refresh_token, csrf_token)

        return {
            "token": access_token,
            "refresh_token": refresh_token,
            "user": user,
            "message": "ایمیل شما با موفقیت تایید شد و وارد حساب شدید",
        }

    @classmethod
    async def resend_verification(cls, email: str) -> Dict[str, Any]:
        """Resend a new verification code adhering to 60s cooldown limit."""
        user = await User.find_one(User.email == email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="کاربری با این ایمیل یافت نشد",
            )

        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="حساب کاربری شما قبلاً تایید شده است",
            )

        code, remaining = await OTPService.create_verification_code(
            user_id=str(user.id), email=email, code_type="email_verification"
        )

        if remaining:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"لطفاً {remaining} ثانیه دیگر مجدداً تلاش کنید",
            )

        if code:
            EmailService.send_verification_email(
                to_email=user.email, name=user.name, code=code
            )

        return {"message": "کد تایید جدید به ایمیل شما ارسال شد"}

    @classmethod
    async def login_user(
        cls, response: Response, email: str, password: str
    ) -> Dict[str, Any]:
        """Authenticate user credentials and check email verification status."""
        user = await User.find_one(User.email == email)
        if not user or not cls.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ایمیل یا رمز عبور اشتباه است",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="حساب کاربری شما غیرفعال شده است",
            )

        # Require email verification for password accounts
        if not user.is_verified and user.provider == "local":
            # Send new code if needed
            code, remaining = await OTPService.create_verification_code(
                user_id=str(user.id), email=email, code_type="email_verification"
            )
            if code:
                EmailService.send_verification_email(
                    to_email=user.email, name=user.name, code=code
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "حساب کاربری شما تایید نشده است. لطفاً ابتدا ایمیل خود را تایید کنید.",
                    "requires_verification": True,
                    "email": user.email,
                },
            )

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        csrf_token = generate_csrf_token()
        set_auth_cookies(response, access_token, refresh_token, csrf_token)

        return {
            "token": access_token,
            "refresh_token": refresh_token,
            "user": user,
            "message": "ورود با موفقیت انجام شد",
        }

    @classmethod
    async def forgot_password(cls, email: str) -> Dict[str, Any]:
        """Send password reset 4-digit code (protects against email enumeration)."""
        user = await User.find_one(User.email == email)
        generic_msg = (
            "اگر حساب کاربری با این ایمیل وجود داشته باشد، کد بازیابی ارسال گردید"
        )

        if not user:
            return {"message": generic_msg}

        code, remaining = await OTPService.create_verification_code(
            user_id=str(user.id), email=email, code_type="password_reset"
        )

        if remaining:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"لطفاً {remaining} ثانیه دیگر مجدداً تلاش کنید",
            )

        if code:
            EmailService.send_password_reset_email(
                to_email=user.email, name=user.name, code=code
            )

        return {"message": generic_msg}

    @classmethod
    async def verify_reset_code(cls, email: str, code: str) -> Dict[str, Any]:
        """Verify the 4-digit password reset code without burning it before password entry."""
        user = await User.find_one(User.email == email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="کاربری با این ایمیل یافت نشد",
            )

        # Check code validity
        is_valid, err_msg = await OTPService.verify_code(
            email=email, code=code, code_type="password_reset"
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg
            )

        return {
            "valid": True,
            "message": "کد بازیابی تایید شد. اکنون می‌توانید رمز عبور جدید را وارد کنید.",
        }

    @classmethod
    async def reset_password(
        cls, email: str, code: str, new_password: str
    ) -> Dict[str, Any]:
        """Reset password using verified OTP code."""
        user = await User.find_one(User.email == email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="کاربری با این ایمیل یافت نشد",
            )

        # Re-verify code or verify if not already used
        is_valid, err_msg = await OTPService.verify_code(
            email=email, code=code, code_type="password_reset"
        )
        if not is_valid and "استفاده شده" not in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg
            )

        user.hashed_password = cls.get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        await user.save()

        return {"message": "رمز عبور شما با موفقیت تغییر یافت"}
