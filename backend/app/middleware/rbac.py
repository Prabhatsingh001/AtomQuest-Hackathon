"""Role-based access control middleware."""

from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.middleware.auth import get_current_active_user


def require_roles(*roles: str):
    """
    FastAPI dependency factory for role-based access control.
    
    Usage: Depends(require_roles('admin', 'manager'))
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(roles)}",
            )
        return current_user

    return role_checker
