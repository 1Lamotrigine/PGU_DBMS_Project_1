from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import Level, Mission, User
from src.services.progression_service import is_mission_unlocked, rank_of


def is_teacher(user: User) -> bool:
    return bool(user.role and user.role.name == "teacher")


async def ensure_mission_accessible(db: AsyncSession, mission: Mission, user: User) -> None:
    """Enforce mission availability on the server (not only in the UI).

    Teachers may access any mission. Students may only access active missions
    whose level is unlocked and whose predecessor in the level is completed.
    """
    if is_teacher(user):
        return

    if not mission.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "MISSION_INACTIVE", "message": "Mission is not available"},
        )

    # Compare the mission's level against the student's unlocked level.
    level = await db.get(Level, mission.level_id)
    level_code = level.code if level else None
    if rank_of(level_code) > (user.unlocked_level_rank or 0):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "LEVEL_LOCKED", "message": "Level is locked for this user"},
        )

    if not await is_mission_unlocked(db, user.id, mission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "MISSION_LOCKED",
                "message": "Complete the previous mission to unlock this one",
            },
        )
