from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.models.models import Level, Mission, UserMissionProgress


async def get_user_progress(db: AsyncSession, user) -> dict:
    completed_result = await db.execute(
        select(func.count(UserMissionProgress.id)).where(
            UserMissionProgress.user_id == user.id,
            UserMissionProgress.is_completed.is_(True),
        )
    )
    completed = int(completed_result.scalar_one())

    total_result = await db.execute(select(func.count(Mission.id)))
    total_missions = int(total_result.scalar_one())

    order = settings.CEFR_ORDER
    user_rank = order.index(user.cefr_level) if user.cefr_level in order else 0
    available_codes = order[: user_rank + 1]

    available_result = await db.execute(
        select(func.count(Mission.id))
        .join(Level, Mission.level_id == Level.id)
        .where(Level.code.in_(available_codes))
    )
    available = int(available_result.scalar_one())

    return {
        "user_id": user.id,
        "name": user.first_name,
        "cefr_level": user.cefr_level,
        "total_xp": user.total_xp,
        "is_calibrated": user.is_calibrated,
        "completed_missions": completed,
        "available_missions": available,
        "total_missions": total_missions,
    }
