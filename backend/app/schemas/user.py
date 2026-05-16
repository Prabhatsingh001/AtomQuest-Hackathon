"""User schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str
    department_id: Optional[UUID] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    manager_id: Optional[UUID] = None


class RegisterRequest(BaseModel):
    """Self-registration — always creates an employee."""

    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=6)
    department_id: Optional[UUID] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    department_id: Optional[UUID]
    department_name: Optional[str]
    manager_id: Optional[UUID]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
