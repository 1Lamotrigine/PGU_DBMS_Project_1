from fastapi import Depends, HTTPException, status

from src.middleware.auth_middleware import get_current_user
from src.models.models import User


def require_roles(*allowed_roles: str):
    """RBAC dependency factory. Usage: Depends(require_roles("teacher"))."""

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        role_name = current_user.role.name if current_user.role else None
        if role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "You do not have permission to perform this action",
                    "details": [f"Required role(s): {', '.join(allowed_roles)}"],
                },
            )
        return current_user

    return dependency
