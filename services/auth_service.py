"""Auth Service orchestrating high-level authentication, session management, token rotation, and security auditing."""

import uuid
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any, List
from fastapi import HTTPException, status, Response, Request
from passlib.context import CryptContext
from beanie import PydanticObjectId

from core.config import settings
from core.security import (
    create_access_token,
    generate_refresh_token,
    hash_token,
    generate_csrf_token,
    set_auth_cookies,
    clear_auth_cookies,
)
from models.user import User
from models.auth_session import AuthSession
from services.otp_service import OTPService
from services.email_service import EmailService
from services.audit_service import AuditLogService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service encapsulating authentication workflows, session tracking, and token rotation."""

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

    @staticmethod
    def _extract_device_info(user_agent: Optional[str]) -> str:
        """Extract a readable device summary from User-Agent header."""
        if not user_agent:
            return "دستگاه ناشناس"
        ua = user_agent.lower()
        if "iphone" in ua or "ipad" in ua:
            return "دستگاه iOS (Apple)"
        if "android" in ua:
            return "دستگاه Android"
        if "windows" in ua:
            return "ویندوز (Windows PC)"
        if "macintosh" in ua or "mac os" in ua:
            return "مک (macOS)"
        if "linux" in ua:
            return "لینوکس (Linux)"
        return "مرورگر وب"

    # ─── Session & Token Rotation Lifecycle ───────────────────────────────────

    @classmethod
    async def create_session(
        cls,
        user: User,
        request: Optional[Request] = None,
        family_id: Optional[str] = None,
    ) -> Tuple[str, str, AuthSession]:
        """Create a new authenticated session with an opaque refresh token and JWT access token."""
        raw_refresh_token = generate_refresh_token()
        token_hash = hash_token(raw_refresh_token)
        token_family_id = family_id or uuid.uuid4().hex

        ip_address = None
        user_agent = None
        if request:
            user_agent = request.headers.get("user-agent")
            forwarded = request.headers.get("x-forwarded-for")
            ip_address = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)

        device_info = cls._extract_device_info(user_agent)
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        session = AuthSession(
            user_id=str(user.id),
            token_family_id=token_family_id,
            refresh_token_hash=token_hash,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            last_used_at=datetime.utcnow(),
            user_agent=user_agent,
            ip_address=ip_address,
            device_info=device_info,
            is_active=True,
        )
        await session.insert()

        access_token = create_access_token(user_id=str(user.id), session_id=str(session.id))
        return access_token, raw_refresh_token, session

    @classmethod
    async def rotate_refresh_token(
        cls, raw_token: str, request: Optional[Request] = None
    ) -> Tuple[str, str, AuthSession]:
        """Validate an existing refresh token, detect reuse attacks, and perform atomic token rotation."""
        token_hash = hash_token(raw_token)
        session = await AuthSession.find_one({"refresh_token_hash": token_hash})

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="توکن بازنشانی نامعتبر است",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # ─── REUSE DETECTION ──────────────────────────────────────────────────
        # If a token that has already been revoked or replaced is presented,
        # it indicates token theft. Invalidate the entire token family immediately.
        if session.revoked_at is not None or not session.is_active:
            # Revoke all sessions in this token family
            await AuthSession.find(
                {"token_family_id": session.token_family_id}
            ).set({"is_active": False, "revoked_at": datetime.utcnow()})

            # Fetch user to log the security alarm
            try:
                user = await User.get(PydanticObjectId(session.user_id))
                if user:
                    await AuditLogService.log_action(
                        user=user,
                        action="SECURITY_ALERT_REFRESH_REUSE",
                        resource="auth_session",
                        details={
                            "token_family_id": session.token_family_id,
                            "compromised_session_id": str(session.id),
                            "action": "All sessions in family terminated due to token reuse",
                        },
                        request=request,
                    )
            except Exception:
                pass

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="تلاش برای استفاده مجدد از توکن باطل‌شده شناسایی شد. جهت امنیت حساب، کلیه نشست‌های مرتبط بسته شدند.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # ─── EXPIRATION CHECK ─────────────────────────────────────────────────
        if session.is_expired:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            await session.save()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="نشست شما منقضی شده است. لطفاً مجدداً وارد شوید.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # ─── USER VALIDATION ──────────────────────────────────────────────────
        user = await User.get(PydanticObjectId(session.user_id))
        if not user or not user.is_active:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            await session.save()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="کاربر یافت نشد یا حساب کاربری غیرفعال است",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # ─── ATOMIC ROTATION ──────────────────────────────────────────────────
        new_raw_refresh_token = generate_refresh_token()
        new_token_hash = hash_token(new_raw_refresh_token)

        ip_address = None
        user_agent = None
        if request:
            user_agent = request.headers.get("user-agent")
            forwarded = request.headers.get("x-forwarded-for")
            ip_address = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)

        device_info = cls._extract_device_info(user_agent or session.user_agent)
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Create new successor session in the same token family
        new_session = AuthSession(
            user_id=str(user.id),
            token_family_id=session.token_family_id,
            refresh_token_hash=new_token_hash,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            last_used_at=datetime.utcnow(),
            user_agent=user_agent or session.user_agent,
            ip_address=ip_address or session.ip_address,
            device_info=device_info,
            is_active=True,
        )
        await new_session.insert()

        # Invalidate the old session record
        session.revoked_at = datetime.utcnow()
        session.replaced_by = str(new_session.id)
        session.is_active = False
        session.last_used_at = datetime.utcnow()
        await session.save()

        # Issue new short-lived access token
        new_access_token = create_access_token(
            user_id=str(user.id), session_id=str(new_session.id)
        )

        return new_access_token, new_raw_refresh_token, new_session

    @classmethod
    async def revoke_session_by_token(cls, raw_token: str) -> None:
        """Revoke a specific session matching the given refresh token."""
        token_hash = hash_token(raw_token)
        session = await AuthSession.find_one({"refresh_token_hash": token_hash})
        if session:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            await session.save()

    @classmethod
    async def revoke_session_by_id(cls, session_id: str, user_id: str) -> bool:
        """Revoke a specific session belonging to the user by session ID."""
        session = await AuthSession.get(PydanticObjectId(session_id))
        if session and session.user_id == user_id:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            await session.save()
            return True
        return False

    @classmethod
    async def revoke_all_user_sessions(cls, user_id: str) -> None:
        """Revoke all active sessions belonging to the user across all devices."""
        await AuthSession.find(
            {"user_id": user_id, "is_active": True}
        ).set({"is_active": False, "revoked_at": datetime.utcnow()})

    @classmethod
    async def get_user_sessions(
        cls, user_id: str, current_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all active, non-expired sessions for a user."""
        current_hash = hash_token(current_token) if current_token else None
        now = datetime.utcnow()

        sessions = await AuthSession.find(
            {
                "user_id": user_id,
                "is_active": True,
                "revoked_at": None,
                "expires_at": {"$gt": now},
            }
        ).sort("-created_at").to_list()

        results = []
        for s in sessions:
            results.append({
                "id": str(s.id),
                "token_family_id": s.token_family_id,
                "created_at": s.created_at,
                "expires_at": s.expires_at,
                "last_used_at": s.last_used_at,
                "user_agent": s.user_agent,
                "ip_address": s.ip_address,
                "device_info": s.device_info,
                "is_current": (s.refresh_token_hash == current_hash),
            })
        return results

    # ─── User Registration & Verification Workflows ───────────────────────────

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
            role="user",
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
        cls, response: Response, email: str, code: str, request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """Verify user's email with 4-digit code and create an authenticated session."""
        user = await User.find_one(User.email == email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="کاربری با این ایمیل یافت نشد",
            )

        if not user.is_verified:
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

        # Create new session
        access_token, refresh_token, _ = await cls.create_session(user, request=request)
        csrf_token = generate_csrf_token()
        set_auth_cookies(response, refresh_token=refresh_token, csrf_token=csrf_token, access_token=access_token)

        await AuditLogService.log_action(
            user=user,
            action="EMAIL_VERIFIED_LOGIN",
            resource="user",
            details={"email": user.email},
            request=request,
        )

        return {
            "token": access_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
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
        cls, response: Response, email: str, password: str, request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """Authenticate user credentials, enforce activation, and create an authenticated session."""
        user = await User.find_one(User.email == email)
        if not user or not cls.verify_password(password, user.hashed_password):
            # Log failed login attempt if user exists or generic
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

        # Create session & set cookies
        access_token, refresh_token, session = await cls.create_session(user, request=request)
        csrf_token = generate_csrf_token()
        set_auth_cookies(response, refresh_token=refresh_token, csrf_token=csrf_token, access_token=access_token)

        await AuditLogService.log_action(
            user=user,
            action="LOGIN_SUCCESS",
            resource="user",
            details={"session_id": str(session.id)},
            request=request,
        )

        return {
            "token": access_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
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
        cls, email: str, code: str, new_password: str, request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """Reset password using verified OTP code and revoke all existing sessions."""
        user = await User.find_one(User.email == email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="کاربری با این ایمیل یافت نشد",
            )

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

        # Revoke all existing sessions for security on password change
        await cls.revoke_all_user_sessions(str(user.id))

        await AuditLogService.log_action(
            user=user,
            action="PASSWORD_RESET_SUCCESS",
            resource="user",
            details={"email": user.email},
            request=request,
        )

        return {"message": "رمز عبور شما با موفقیت تغییر یافت. لطفاً با رمز عبور جدید وارد شوید."}
