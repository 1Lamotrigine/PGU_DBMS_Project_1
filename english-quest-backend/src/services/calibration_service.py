from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.models.models import CalibrationQuestion, Level, Mission, Task, User, UserMissionProgress
from src.services.progression_service import rank_of


def _level_for_percentage(percent: float) -> str:
    result = "A1"
    for code in settings.CEFR_ORDER:
        if percent >= settings.CALIBRATION_THRESHOLDS[code]:
            result = code
    return result


async def submit_calibration(db: AsyncSession, user: User, payload) -> dict:
    if user.is_calibrated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ALREADY_CALIBRATED", "message": "User has already passed calibration"},
        )

    result = await db.execute(select(CalibrationQuestion))
    all_questions = {q.id: q for q in result.scalars().all()}
    if not all_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NO_QUESTIONS", "message": "No calibration questions available"},
        )

    submitted = {answer.question_id: answer.selected_option for answer in payload.answers}
    # Require the full server-side set: a single answer must not yield a level.
    if set(submitted) != set(all_questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INCOMPLETE_CALIBRATION",
                "message": "Answer every calibration question",
            },
        )

    correct = sum(
        1
        for question_id, option in submitted.items()
        if all_questions[question_id].correct_option == option
    )
    percent = correct / len(all_questions) * 100.0
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

        # Sum XP per mission in one query instead of one query per mission.
        xp_by_mission = dict(
            (
                await db.execute(
                    select(Task.mission_id, func.coalesce(func.sum(Task.xp_reward_first), 0))
                    .where(Task.mission_id.in_([m.id for m in missions]))
                    .group_by(Task.mission_id)
                )
            ).all()
        ) if missions else {}

        for mission in missions:
            progress = (
                await db.execute(
                    select(UserMissionProgress).where(
                        UserMissionProgress.user_id == user.id,
                        UserMissionProgress.mission_id == mission.id,
                    )
                )
            ).scalar_one_or_none()

            # Never re-award or overwrite an already completed mission.
            if progress is not None and progress.is_completed:
                continue

            if progress is None:
                progress = UserMissionProgress(user_id=user.id, mission_id=mission.id)
                db.add(progress)
            progress.is_completed = True
            progress.tests_passed = True
            progress.pronunciation_passed = True
            progress.best_score_percentage = 100.0
            progress.completion_count = max(progress.completion_count or 0, 1)
            progress.last_completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            auto_completed += 1
            starting_xp += int(xp_by_mission.get(mission.id, 0))

    user.cefr_level = cefr_code
    user.level_id = level.id if level else None
    user.is_calibrated = True
    # Calibration determines the starting unlocked level.
    user.unlocked_level_rank = rank_of(cefr_code)

    new_total = user.total_xp or 0
    try:
        if starting_xp:
            new_total = await db.scalar(
                update(User)
                .where(User.id == user.id)
                .values(total_xp=func.coalesce(User.total_xp, 0) + starting_xp)
                .returning(User.total_xp)
            )
        # One transaction: level change, auto-completed missions and start XP.
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return {
        "cefr_level": cefr_code,
        "total_xp": new_total,
        "auto_completed_missions": auto_completed,
        "score_percentage": round(percent, 2),
    }
