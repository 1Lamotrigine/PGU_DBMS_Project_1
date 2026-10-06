from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.models import User


async def get_user_with_role(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.email == email)
    )
    return result.scalar_one_or_none()
