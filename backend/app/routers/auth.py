"""Auth router — login, register, logout, refresh, me."""

import logging
import redis
import hashlib
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.config import get_settings
from app.models.user import User
from app.models.department import Department
from app.schemas.user import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshRequest,
    AccessTokenResponse,
    UserResponse,
)
from app.utils.jwt import create_access_token, create_refresh_token, decode_token
from app.middleware.auth import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()
logger = logging.getLogger(__name__)

# Redis for token blacklist
redis_kwargs = {"decode_responses": True}
if settings.REDIS_URL.startswith("rediss://"):
    redis_kwargs["ssl_cert_reqs"] = "required"
redis_client = redis.from_url(settings.REDIS_URL, **redis_kwargs)


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new employee account.

    Args:
        data: Registration schema containing email, name, password, and optional department.
        db: Active database session.

    Returns:
        UserResponse: The newly created inactive employee account.

    Raises:
        HTTPException: If the email already exists or department is invalid.
    """
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    if data.department_id:
        department = (
            db.query(Department).filter(Department.id == data.department_id).first()
        )
        if not department or not department.is_active: # type: ignore
            raise HTTPException(
                status_code=400, detail="Invalid or inactive department"
            )

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=pwd_context.hash(data.password),
        role="employee",
        department_id=data.department_id,
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user credentials and generate active JWT session tokens.

    Args:
        data: Login schema containing email and plaintext password.
        db: Active database session.

    Returns:
        TokenResponse: Access and refresh tokens alongside user metadata.

    Raises:
        HTTPException: If credentials fail verification or the account is inactive.
    """
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not pwd_context.verify(data.password, user.hashed_password):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    try:
        redis_client.setex(
            f"refresh:{str(user.id)}:{token_hash}",
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            "1",
        )
    except redis.RedisError as e:
        logger.warning(f"Redis cache unavailable during login: {e}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    """Issue a new access token using an unrevoked refresh token.

    Args:
        data: Request payload containing the active refresh token.
        db: Active database session.

    Returns:
        AccessTokenResponse: A fresh access token and rotated refresh token pair.

    Raises:
        HTTPException: If the refresh token is invalid, expired, or blacklisted.
    """
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    try:
        user_uuid = UUID(str(user_id))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_hash = hashlib.sha256(data.refresh_token.encode()).hexdigest()
    try:
        if redis_client.get(f"blacklist:{token_hash}"):
            raise HTTPException(status_code=401, detail="Token has been revoked")

        stored = redis_client.get(f"refresh:{str(user_uuid)}:{token_hash}")
        if not stored:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except redis.RedisError as e:
        logger.warning(f"Redis cache unavailable during refresh check: {e}")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user or not user.is_active:  # type: ignore
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token({"sub": str(user_uuid)})
    refresh_token = create_refresh_token({"sub": str(user_uuid)})

    new_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    try:
        redis_client.delete(f"refresh:{str(user_uuid)}:{token_hash}")
        redis_client.setex(
            f"refresh:{str(user_uuid)}:{new_hash}",
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            "1",
        )
        redis_client.setex(
            f"blacklist:{token_hash}",
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            "1",
        )
    except redis.RedisError as e:
        logger.warning(f"Redis cache unavailable during refresh token rotation: {e}")

    return AccessTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/logout")
def logout(
    data: Optional[RefreshRequest] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Invalidate current session tokens and revoke active refresh tokens.

    Args:
        data: Optional payload containing specific refresh token to revoke.
        current_user: Currently authenticated user entity.

    Returns:
        dict: Success confirmation message.
    """
    try:
        if data and data.refresh_token:
            token_hash = hashlib.sha256(data.refresh_token.encode()).hexdigest()
            if redis_client.get(f"refresh:{str(current_user.id)}:{token_hash}"):
                redis_client.delete(f"refresh:{str(current_user.id)}:{token_hash}")
                redis_client.setex(
                    f"blacklist:{token_hash}",
                    settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
                    "1",
                )
        else:
            for key in redis_client.scan_iter(f"refresh:{str(current_user.id)}:*"):
                token_hash = key.split(":")[-1]
                redis_client.delete(key)
                redis_client.setex(
                    f"blacklist:{token_hash}",
                    settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
                    "1",
                )
    except redis.RedisError as e:
        logger.warning(f"Redis cache unavailable during logout: {e}")

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_active_user)):
    """Retrieve metadata and profile information for the authenticated user.

    Args:
        current_user: The authenticated user entity.

    Returns:
        UserResponse: Serialized profile data.
    """
    return UserResponse.model_validate(current_user)

