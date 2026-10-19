"""Level/mission progression rules and the XP leaderboard.

Progression model
-----------------
* Inside a level missions unlock sequentially: mission with ``order_index = 1``
  is always available, and mission ``n + 1`` unlocks once mission ``n`` is
  completed.
* A level unlocks when the student has earned enough XP *within that level*
  (``LEVEL_UNLOCK_RATIO`` of the level's maximum first-time XP) or has completed
  every mission of the level.
* The unlocked level is tracked separately from ``cefr_level`` (which is set only
  by calibration) via ``users.unlocked_level_rank``.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.models.models import Level, Mission, Task, User, UserMissionProgress

# Share of a level's maximum XP required to unlock the next level.
LEVEL_UNLOCK_RATIO = 0.7


def rank_of(code: str | None) -> int:
    order = settings.CEFR_ORDER
    return order.index(code) if code in order else 0


def code_of(rank: int) -> str:
    order = settings.CEFR_ORDER
    return order[rank] if 0 <= rank < len(order) else order[-1]


async def level_max_xp(db: AsyncSession, level_id: int) -> int:
    """Maximum first-time XP obtainable across all missions of a level."""
    result = await db.execute(
        select(func.coalesce(func.sum(Task.xp_reward_first), 0))
        .join(Mission, Task.mission_id == Mission.id)
        .where(Mission.level_id == level_id, Mission.is_active.is_(True))
    )
    return int(result.scalar_one())


async def level_earned_xp(db: AsyncSession, user_id: int, level_id: int) -> int:
    """XP the student has actually earned across the missions of a level."""
    result = await db.execute(
        select(func.coalesce(func.sum(UserMissionProgress.xp_earned), 0))
        .join(Mission, UserMissionProgress.mission_id == Mission.id)
        .where(UserMissionProgress.user_id == user_id, Mission.level_id == level_id)
    )
    return int(result.scalar_one())


async def _level_completed(db: AsyncSession, user_id: int, level_id: int) -> bool:
    total = await db.scalar(
        select(func.count(Mission.id)).where(Mission.level_id == level_id, Mission.is_active.is_(True))
    )
    total = int(total or 0)
    if total == 0:
        return False
    completed = await db.scalar(
        select(func.count(UserMissionProgress.id))
        .join(Mission, UserMissionProgress.mission_id == Mission.id)
        .where(
            UserMissionProgress.user_id == user_id,
            Mission.level_id == level_id,
            UserMissionProgress.is_completed.is_(True),
        )
    )
    return int(completed or 0) >= total


async def recompute_unlocked_rank(db: AsyncSession, user: User) -> int:
    """Recompute and persist how far the student may advance.

    Starts from the calibrated level and walks up while each level is either
    fully completed or has enough earned XP.
    """
    levels = (
        await db.execute(select(Level).order_by(Level.id))
    ).scalars().all()
    by_rank = {rank_of(level.code): level for level in levels}

    unlocked = rank_of(user.cefr_level)
    while True:
        level = by_rank.get(unlocked)
        if level is None:
            break
        if await _level_completed(db, user.id, level.id):
            unlocked += 1
            continue
        maximum = await level_max_xp(db, level.id)
        earned = await level_earned_xp(db, user.id, level.id)
        if maximum > 0 and earned >= LEVEL_UNLOCK_RATIO * maximum:
            unlocked += 1
            continue
        break

    unlocked = min(unlocked, len(settings.CEFR_ORDER) - 1)
    if unlocked > (user.unlocked_level_rank or 0):
        user.unlocked_level_rank = unlocked
    return user.unlocked_level_rank or 0


async def is_mission_unlocked(db: AsyncSession, user_id: int, mission: Mission) -> bool:
    """True if the mission's predecessor in the same level is completed."""
    if mission.order_index <= 1:
        return True
    predecessor = (
        await db.execute(
            select(Mission).where(
                Mission.level_id == mission.level_id,
                Mission.order_index == mission.order_index - 1,
            )
        )
    ).scalar_one_or_none()
    if predecessor is None:
        return True
    progress = (
        await db.execute(
            select(UserMissionProgress).where(
                UserMissionProgress.user_id == user_id,
                UserMissionProgress.mission_id == predecessor.id,
            )
        )
    ).scalar_one_or_none()
    return bool(progress and progress.is_completed)


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------
async def get_leaderboard(db: AsyncSession, limit: int = 10) -> list[dict]:
    """Top students by total XP. Emails are never exposed."""
    result = await db.execute(
        select(User)
        .where(User.role.has(name="student"))
        .order_by(User.total_xp.desc(), User.id.asc())
        .limit(limit)
    )
    users = list(result.scalars().all())
    return [
        {"rank": i + 1, "name": f"{u.first_name} {u.last_name}".strip(), "total_xp": u.total_xp or 0}
        for i, u in enumerate(users)
    ]
