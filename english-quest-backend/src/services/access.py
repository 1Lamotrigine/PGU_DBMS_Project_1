from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.models.models import Level, Mission, User


def _rank(code: str | None) -> int:
    order = settings.CEFR_ORDER
    return order.index(code) if code in order else 0


def is_teacher(user: User) -> bool:
    return bool(user.role and user.role.name == "teacher")


async def ensure_mission_accessible(db: AsyncSession, mission: Mission, user: User) -> None:
    """Enforce mission availability on the server (not only in the UI).

    Teachers may access any mission. Students may only access active missions
    whose CEFR level is not above their current level.
    """
    if is_teacher(user):
        return

    if not mission.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "MISSION_INACTIVE", "message": "Mission is not available"},
        )

    level = await db.get(Level, mission.level_id)
    level_code = level.code if level else None
    if _rank(level_code) > _rank(user.cefr_level):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "MISSION_LOCKED", "message": "Mission level is locked for this user"},
        )
