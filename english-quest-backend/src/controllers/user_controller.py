from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.middleware.auth_middleware import get_current_user
from src.models.models import User
from src.services.user_lookup import get_user_with_role
from src.services.user_service import get_user_progress


async def my_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await get_user_progress(db, current_user)


async def student_progress_preview(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    target = await get_user_with_role(db, student_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Student not found"},
        )
    return await get_user_progress(db, target)
