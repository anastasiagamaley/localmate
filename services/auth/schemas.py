from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from database import AccountType


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    account_type: AccountType = AccountType.regular

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    account_type: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserPublic(BaseModel):
    id: str
    email: str
    account_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class VerifyTokenRequest(BaseModel):
    token: str


class VerifyTokenResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    account_type: Optional[str] = None
