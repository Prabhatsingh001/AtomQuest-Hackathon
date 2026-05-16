"""User schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user profile attributes.

    Attributes:
        email: Validated user email address.
        full_name: Full display name.
        role: Assigned RBAC role ('employee', 'manager', 'hr', 'admin').
        department_id: Optional assigned department UUID.
    """
    email: EmailStr
    full_name: str
    role: str
    department_id: Optional[UUID] = None


class UserCreate(UserBase):
    """Schema for administrator account creation.

    Attributes:
        password: Plaintext password (min 6 characters).
        manager_id: Optional supervising manager account UUID.
    """
    password: str = Field(..., min_length=6)
    manager_id: Optional[UUID] = None


class RegisterRequest(BaseModel):
    """Schema for public user self-registration. Default role is 'employee'.

    Attributes:
        email: Validated email address.
        full_name: Display name.
        password: Plaintext password (min 6 characters).
        department_id: Optional initial department assignment UUID.
    """
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=6)
    department_id: Optional[UUID] = None


class UserUpdate(BaseModel):
    """Schema for modifying existing user profile attributes or assignment relationships.

    Attributes:
        full_name: Optional updated display name.
        role: Optional updated RBAC role.
        department_id: Optional updated department UUID.
        manager_id: Optional updated manager UUID.
        is_active: Optional active status toggle.
    """
    full_name: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Serialized user account payload returned by API endpoints.

    Attributes:
        id: Unique user account UUID.
        email: Email address.
        full_name: Display name.
        role: Active RBAC role.
        department_id: Assigned department UUID.
        department_name: Resolved display name of assigned department.
        manager_id: Supervising manager account UUID.
        is_active: True if account is enabled for login.
        created_at: ISO-8601 creation timestamp.
    """
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
    """Schema for authentication credentials submission.

    Attributes:
        email: Registered account email.
        password: Plaintext account password.
    """
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Authentication success payload containing JWT tokens and profile metadata.

    Attributes:
        access_token: Encrypted short-lived authorization JWT.
        refresh_token: Encrypted long-lived refresh JWT.
        token_type: Token schema descriptor (defaults to 'bearer').
        user: Serialized authenticated profile record.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    """Schema for submitting a refresh token to obtain a new access session.

    Attributes:
        refresh_token: Unexpired valid refresh token string.
    """
    refresh_token: str


class AccessTokenResponse(BaseModel):
    """Token refresh success payload returning renewed JWT credentials.

    Attributes:
        access_token: New short-lived authorization JWT.
        refresh_token: Rotated or maintained refresh JWT.
        token_type: Schema descriptor ('bearer').
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
