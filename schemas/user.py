"""User and Authentication Pydantic Schemas."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, description="Full Name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    phone: Optional[str] = Field(None, description="Phone number")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


class PasswordChange(BaseModel):
    currentPassword: str
    newPassword: str = Field(..., min_length=6)


class TokenRefreshPayload(BaseModel):
    refresh_token: Optional[str] = Field(
        None, description="Optional refresh token string for non-browser clients"
    )


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., description="Google ID Token received from Google Sign-In")


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=4, description="4-digit verification code")


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=4, description="4-digit reset code")


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=4, description="4-digit reset code")
    new_password: str = Field(..., min_length=6, description="New password (min 6 chars)")


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    avatar: Optional[str] = None
    provider: Optional[str] = "local"
    email_verified: Optional[bool] = False
    is_verified: Optional[bool] = False
    createdAt: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900
    user: Optional[UserResponse] = None


class AuthSessionResponse(BaseModel):
    id: str
    token_family_id: str
    created_at: datetime
    expires_at: datetime
    last_used_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    device_info: Optional[str] = None
    is_current: bool = False
