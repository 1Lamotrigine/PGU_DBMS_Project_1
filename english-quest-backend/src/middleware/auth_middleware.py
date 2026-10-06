import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.models.models import User
from src.services.security import decode_access_token
from src.services.user_lookup import get_user_with_role

security = HTTPBearer(auto_error=False)


def _unauthorized(message: str = "Invalid or missing token") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "UNAUTHORIZED", "message": message, "details": []},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise _unauthorized()

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token has expired")
    except jwt.PyJWTError:
        raise _unauthorized("Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise _unauthorized()

    user = await get_user_with_role(db, int(user_id))
    if user is None:
        raise _unauthorized("User no longer exists")
    return user
