from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.models.models import Mission, Task, User, UserMissionProgress


async def _mission_or_404(db: AsyncSession, mission_id: int) -> Mission:
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if mission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Mission not found"},
        )
    return mission


async def _progress_or_none(db: AsyncSession, user_id: int, mission_id: int) -> UserMissionProgress | None:
    result = await db.execute(
        select(UserMissionProgress).where(
            UserMissionProgress.user_id == user_id,
            UserMissionProgress.mission_id == mission_id,
        )
    )
    return result.scalar_one_or_none()


async def _xp_sum(db: AsyncSession, mission_id: int, field) -> int:
    result = await db.execute(select(func.coalesce(func.sum(field), 0)).where(Task.mission_id == mission_id))
    return int(result.scalar_one())


async def submit_tests(db: AsyncSession, mission_id: int, user: User, payload) -> dict:
    await _mission_or_404(db, mission_id)

    percent = payload.correctAnswers / payload.totalQuestions * 100.0
    passed = percent >= settings.GAME_PASS_THRESHOLD

    progress = await _progress_or_none(db, user.id, mission_id)
    if progress is None:
        progress = UserMissionProgress(user_id=user.id, mission_id=mission_id)
        db.add(progress)

    if passed:
        progress.tests_passed = True

    await db.commit()

    return {"tests_passed": progress.tests_passed, "percent": round(percent, 2), "passed": passed}


async def submit_pronunciation(db: AsyncSession, mission_id: int, user: User, payload) -> dict:
    await _mission_or_404(db, mission_id)

    progress = await _progress_or_none(db, user.id, mission_id)
    if progress is None or not progress.tests_passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "TESTS_REQUIRED", "message": "Pass the test block before pronunciation"},
        )

    percent = payload.correctAnswers / payload.totalQuestions * 100.0 if payload.totalQuestions else 0.0
    passed = percent >= settings.GAME_PASS_THRESHOLD
    if passed:
        progress.pronunciation_passed = True

    await db.commit()

    return {
        "pronunciation_passed": progress.pronunciation_passed,
        "percent": round(percent, 2),
        "passed": passed,
    }


async def submit_game(db: AsyncSession, mission_id: int, user: User, payload) -> dict:
    await _mission_or_404(db, mission_id)

    progress = await _progress_or_none(db, user.id, mission_id)
    if progress is None or not progress.pronunciation_passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PRONUNCIATION_REQUIRED", "message": "Pass pronunciation before the game"},
        )

    percent = payload.correctAnswers / payload.totalQuestions * 100.0
    if percent < settings.GAME_PASS_THRESHOLD:
        return {"success": False, "percent": round(percent, 2), "xp_awarded": 0, "total_xp": user.total_xp}

    first_time = progress.completion_count == 0

    xp = await _xp_sum(db, mission_id, Task.xp_reward_first if first_time else Task.xp_reward_repeat)

    progress.is_completed = True
    progress.completion_count = (progress.completion_count or 0) + 1
    progress.best_score_percentage = max(progress.best_score_percentage or 0.0, percent)
    progress.last_completed_at = datetime.utcnow()

    user.total_xp = (user.total_xp or 0) + xp

    await db.commit()

    return {
        "success": True,
        "percent": round(percent, 2),
        "xp_awarded": xp,
        "total_xp": user.total_xp,
        "completion_count": progress.completion_count,
    }
