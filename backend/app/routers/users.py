"""Users router — user profile endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.middleware.auth import get_current_active_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info."""
    return UserResponse.model_validate(current_user)


@router.get("/team")
def get_team(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get direct reports for a manager."""
    reports = db.query(User).filter(User.manager_id == current_user.id).all()
    return [UserResponse.model_validate(u) for u in reports]
