from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.models.models import CalibrationQuestion, Level, Mission, Task, UserMissionProgress


def _level_for_percentage(percent: float) -> str:
    result = "A1"
    for code in settings.CEFR_ORDER:
        if percent >= settings.CALIBRATION_THRESHOLDS[code]:
            result = code
    return result


async def submit_calibration(db: AsyncSession, user, payload) -> dict:
    if user.is_calibrated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ALREADY_CALIBRATED", "message": "User has already passed calibration"},
        )

    question_ids = [answer.question_id for answer in payload.answers]
    result = await db.execute(
        select(CalibrationQuestion).where(CalibrationQuestion.id.in_(question_ids))
    )
    questions = {q.id: q for q in result.scalars().all()}
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NO_QUESTIONS", "message": "None of the submitted questions exist"},
        )

    correct = sum(
        1
        for answer in payload.answers
        if (q := questions.get(answer.question_id)) and q.correct_option == answer.selected_option
    )
    percent = correct / len(payload.answers) * 100.0
    cefr_code = _level_for_percentage(percent)

    level_result = await db.execute(select(Level).where(Level.code == cefr_code))
    level = level_result.scalar_one_or_none()

    order = settings.CEFR_ORDER
    below_codes = order[: order.index(cefr_code)]
    auto_completed = 0
    starting_xp = 0

    if below_codes:
        level_rows = await db.execute(select(Level).where(Level.code.in_(below_codes)))
        lower_ids = [lvl.id for lvl in level_rows.scalars().all()]
        missions_result = await db.execute(select(Mission).where(Mission.level_id.in_(lower_ids)))
        missions = list(missions_result.scalars().all())

        for mission in missions:
            xp_result = await db.execute(
                select(func.coalesce(func.sum(Task.xp_reward_first), 0)).where(Task.mission_id == mission.id)
            )
            starting_xp += int(xp_result.scalar_one())

            progress_result = await db.execute(
                select(UserMissionProgress).where(
                    UserMissionProgress.user_id == user.id,
                    UserMissionProgress.mission_id == mission.id,
                )
            )
            progress = progress_result.scalar_one_or_none()
            if progress is None:
                progress = UserMissionProgress(user_id=user.id, mission_id=mission.id)
                db.add(progress)
            progress.is_completed = True
            progress.tests_passed = True
            progress.pronunciation_passed = True
            progress.best_score_percentage = 100.0
            progress.completion_count = 1
            progress.last_completed_at = datetime.utcnow()
            auto_completed += 1

    user.cefr_level = cefr_code
    user.level_id = level.id if level else None
    user.is_calibrated = True
    user.total_xp = (user.total_xp or 0) + starting_xp

    await db.commit()

    return {
        "cefr_level": cefr_code,
        "total_xp": user.total_xp,
        "auto_completed_missions": auto_completed,
        "score_percentage": round(percent, 2),
    }
