import json
import re
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.settings import settings
from src.models.models import (
    Mission,
    MissionAttempt,
    Question,
    Task,
    User,
    UserMissionProgress,
    VocabularyItem,
)
from src.services.access import ensure_mission_accessible
from src.services.progression_service import recompute_unlocked_rank

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Number of vocabulary items issued for a single arcade attempt.
GAME_ITEMS = 10


def _normalize_tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _word_matches(spoken: str, target: str) -> bool:
    """Whole-token match so "car" does not match "carpet"."""
    spoken_tokens = _normalize_tokens(spoken)
    target_tokens = _normalize_tokens(target)
    if not target_tokens or not spoken_tokens:
        return False
    if len(target_tokens) == 1:
        return target_tokens[0] in spoken_tokens
    joined_spoken = " ".join(spoken_tokens)
    return " ".join(target_tokens) in joined_spoken


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


async def _xp_sum(
    db: AsyncSession, mission_id: int, field, task_types: list[str] | None = None
) -> int:
    query = select(func.coalesce(func.sum(field), 0)).where(Task.mission_id == mission_id)
    if task_types is not None:
        query = query.where(Task.task_type.in_(task_types))
    result = await db.execute(query)
    return int(result.scalar_one())


async def _mission_questions(db: AsyncSession, mission_id: int) -> dict[int, Question]:
    """All questions that belong to the mission's test block."""
    result = await db.execute(
        select(Question)
        .join(Task, Question.task_id == Task.id)
        .options(selectinload(Question.options))
        .where(
            Task.mission_id == mission_id,
            Task.task_type.in_(["multiple_choice", "fill_blank", "image_match"]),
        )
    )
    return {q.id: q for q in result.scalars().all()}


async def _level_vocabulary(db: AsyncSession, mission: Mission) -> list[VocabularyItem]:
    result = await db.execute(
        select(VocabularyItem)
        .where(VocabularyItem.level_id == mission.level_id)
        .order_by(VocabularyItem.id)
    )
    return list(result.scalars().all())


async def _mission_grammar_questions(db: AsyncSession, mission_id: int) -> dict[int, Question]:
    """Questions of the mission's grammar block (task_type = 'grammar')."""
    result = await db.execute(
        select(Question)
        .join(Task, Question.task_id == Task.id)
        .options(selectinload(Question.options))
        .where(Task.mission_id == mission_id, Task.task_type == "grammar")
        .order_by(Question.id)
    )
    return {q.id: q for q in result.scalars().all()}


def _serialize_grammar_question(question: Question) -> dict:
    """Grammar question without the correct flag — students must pick it."""
    return {
        "id": question.id,
        "question_text": question.question_text,
        "question_type": question.question_type,
        "options": [
            {
                "id": option.id,
                "option_text": option.option_text,
                "translation_ru": option.translation_ru,
                "image_url": option.image_url,
            }
            for option in question.options
        ],
    }


def _serialize_vocab(item: VocabularyItem) -> dict:
    return {
        "id": item.id,
        "word_en": item.word_en,
        "word_ru": item.word_ru,
        "transcription": item.transcription,
        "image_url": item.image_url,
    }


# ---------------------------------------------------------------------------
# Attempts
# ---------------------------------------------------------------------------
async def start_attempt(db: AsyncSession, mission_id: int, user: User, module: str = "game") -> dict:
    mission = await _mission_or_404(db, mission_id)
    await ensure_mission_accessible(db, mission, user)

    payload: dict = {"attempt_id": None, "module": module}
    issued_ids: list[int] = []
    if module in ("game", "pronunciation"):
        items = await _level_vocabulary(db, mission)
        if module == "game":
            import random

            items = random.sample(items, min(GAME_ITEMS, len(items)))
        issued_ids = [item.id for item in items]
        payload["items"] = [_serialize_vocab(item) for item in items]
    elif module == "grammar":
        progress = await _progress_or_none(db, user.id, mission_id)
        if progress is None or not progress.game_passed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "GAME_REQUIRED", "message": "Pass the dictionary game before grammar"},
            )
        questions = await _mission_grammar_questions(db, mission_id)
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "NO_GRAMMAR_QUESTIONS", "message": "This mission has no grammar questions"},
            )
        ordered = list(questions.values())
        issued_ids = [q.id for q in ordered]
        payload["questions"] = [_serialize_grammar_question(q) for q in ordered]

    attempt = MissionAttempt(
        user_id=user.id,
        mission_id=mission_id,
        module=module,
        status="in_progress",
        issued=json.dumps(issued_ids),
    )
    db.add(attempt)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(attempt)
    payload["attempt_id"] = attempt.id
    return payload


async def _locked_attempt(db: AsyncSession, attempt_id: int, user: User, mission_id: int) -> MissionAttempt:
    """Load an in-progress attempt and lock it so it can be completed once."""
    result = await db.execute(
        select(MissionAttempt)
        .where(
            MissionAttempt.id == attempt_id,
            MissionAttempt.user_id == user.id,
            MissionAttempt.mission_id == mission_id,
        )
        .with_for_update()
    )
    attempt = result.scalar_one_or_none()
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ATTEMPT_NOT_FOUND", "message": "Attempt not found"},
        )
    return attempt


# ---------------------------------------------------------------------------
# Test block (fully server-graded)
# ---------------------------------------------------------------------------
async def submit_tests(db: AsyncSession, mission_id: int, user: User, payload) -> dict:
    mission = await _mission_or_404(db, mission_id)
    await ensure_mission_accessible(db, mission, user)

    questions = await _mission_questions(db, mission_id)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NO_QUESTIONS", "message": "This mission has no test questions"},
        )

    submitted = {answer.question_id: answer for answer in payload.answers}
    if set(submitted) != set(questions):
        # Require the full, exact set: prevents answering only the easy ones.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INCOMPLETE_ANSWERS", "message": "Answer every question of the mission"},
        )

    correct = 0
    for question_id, answer in submitted.items():
        correct_option = next((o for o in questions[question_id].options if o.is_correct), None)
        if correct_option is None:
            continue
        if answer.option_id is not None:
            if answer.option_id == correct_option.id:
                correct += 1
        elif answer.text is not None:
            if " ".join(_normalize_tokens(answer.text)) == " ".join(
                _normalize_tokens(correct_option.option_text)
            ):
                correct += 1

    percent = correct / len(questions) * 100.0
    passed = percent >= settings.GAME_PASS_THRESHOLD

    progress = await _progress_or_none(db, user.id, mission_id)
    if progress is None:
        progress = UserMissionProgress(user_id=user.id, mission_id=mission_id)
        db.add(progress)
    if passed:
        progress.tests_passed = True
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return {"tests_passed": progress.tests_passed, "percent": round(percent, 2), "passed": passed}


# ---------------------------------------------------------------------------
# Pronunciation block
# ---------------------------------------------------------------------------
async def submit_pronunciation(db: AsyncSession, mission_id: int, user: User, payload) -> dict:
    mission = await _mission_or_404(db, mission_id)
    await ensure_mission_accessible(db, mission, user)

    progress = await _progress_or_none(db, user.id, mission_id)
    if progress is None or not progress.tests_passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "TESTS_REQUIRED", "message": "Pass the test block before pronunciation"},
        )

    percent = await _word_percent(db, mission, payload)
    passed = percent >= settings.GAME_PASS_THRESHOLD
    if passed:
        progress.pronunciation_passed = True
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return {
        "pronunciation_passed": progress.pronunciation_passed,
        "percent": round(percent, 2),
        "passed": passed,
    }


async def _word_percent(db: AsyncSession, mission: Mission, payload, total_override: int | None = None) -> float:
    """Compute the percentage for a word-answer block (game / pronunciation)."""
    if getattr(payload, "answers", None):
        items = {item.id: item for item in await _level_vocabulary(db, mission)}
        correct = 0
        for answer in payload.answers:
            item = items.get(answer.item_id)
            if item is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "INVALID_ITEM", "message": "Unknown vocabulary item"},
                )
            if _word_matches(answer.word, item.word_en):
                correct += 1
        total = total_override if total_override else len(payload.answers)
        return correct / total * 100.0 if total else 0.0

    # Legacy client-reported score (deprecated).
    total = payload.totalQuestions or 0
    return payload.correctAnswers / total * 100.0 if total else 0.0


# ---------------------------------------------------------------------------
# Arcade block (awards XP; requires a server-issued attempt)
# ---------------------------------------------------------------------------
async def submit_game(db: AsyncSession, mission_id: int, user: User, payload) -> dict:
    mission = await _mission_or_404(db, mission_id)
    await ensure_mission_accessible(db, mission, user)

    if payload.attempt_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ATTEMPT_REQUIRED",
                "message": "Start an attempt before submitting the game result",
            },
        )

    attempt = await _locked_attempt(db, payload.attempt_id, user, mission_id)
    if attempt.module != "game":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "WRONG_ATTEMPT_MODULE", "message": "This attempt is not a game attempt"},
        )
    if attempt.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ATTEMPT_ALREADY_COMPLETED", "message": "This attempt was already submitted"},
        )

    progress = await _progress_or_none(db, user.id, mission_id)
    if progress is None or not progress.pronunciation_passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PRONUNCIATION_REQUIRED", "message": "Pass pronunciation before the game"},
        )

    issued_ids = json.loads(attempt.issued or "[]")
    percent = await _word_percent(db, mission, payload, total_override=len(issued_ids) or None)
    passed = percent >= settings.GAME_PASS_THRESHOLD

    completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Everything below is one atomic unit: closing the attempt, awarding XP and
    # updating progress either all succeed together or none of them do.
    try:
        # Complete the attempt exactly once (conditional update guards against races).
        claim = await db.execute(
            update(MissionAttempt)
            .where(MissionAttempt.id == attempt.id, MissionAttempt.status == "in_progress")
            .values(
                status="completed" if passed else "failed",
                score=round(percent, 2),
                completed_at=completed_at,
            )
            .returning(MissionAttempt.id)
        )
        if claim.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "ATTEMPT_ALREADY_COMPLETED",
                    "message": "This attempt was already submitted",
                },
            )

        if not passed:
            await db.commit()
            return {
                "success": False,
                "percent": round(percent, 2),
                "xp_awarded": 0,
                "total_xp": user.total_xp,
            }

        # First completion vs repeat is decided by prior completed attempts.
        completed_before = await db.scalar(
            select(func.count(MissionAttempt.id)).where(
                MissionAttempt.user_id == user.id,
                MissionAttempt.mission_id == mission_id,
                MissionAttempt.module == "game",
                MissionAttempt.status == "completed",
                MissionAttempt.id != attempt.id,
            )
        )
        first_time = int(completed_before or 0) == 0

        xp = await _xp_sum(
            db,
            mission_id,
            Task.xp_reward_first if first_time else Task.xp_reward_repeat,
            task_types=["multiple_choice", "translation", "vocabulary_game"],
        )

        best_score = max(progress.best_score_percentage or 0.0, percent)

        # Atomic XP increment: never read-modify-write total_xp.
        new_total = await db.scalar(
            update(User)
            .where(User.id == user.id)
            .values(total_xp=func.coalesce(User.total_xp, 0) + xp)
            .returning(User.total_xp)
            .execution_options(synchronize_session=False)
        )
        attempt.xp_earned = xp

        # The game is the third of four stages: it marks its own flag but the
        # mission is completed by the grammar stage. Legacy rows that were
        # already completed stay completed.
        new_completion = await db.scalar(
            update(UserMissionProgress)
            .where(
                UserMissionProgress.user_id == user.id,
                UserMissionProgress.mission_id == mission_id,
            )
            .values(
                game_passed=True,
                best_score_percentage=best_score,
                xp_earned=func.coalesce(UserMissionProgress.xp_earned, 0) + xp,
                last_completed_at=func.coalesce(UserMissionProgress.last_completed_at, completed_at),
            )
            .returning(UserMissionProgress.completion_count)
            .execution_options(synchronize_session=False)
        )

        # Recompute how far the student may advance (level unlock by XP or 5/5).
        await recompute_unlocked_rank(db, user)

        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise

    return {
        "success": True,
        "percent": round(percent, 2),
        "xp_awarded": xp,
        "total_xp": new_total,
        "completion_count": new_completion,
    }


# ---------------------------------------------------------------------------
# Grammar block (fourth stage: click the correct word form)
# ---------------------------------------------------------------------------
async def submit_grammar(db: AsyncSession, mission_id: int, user: User, payload) -> dict:
    mission = await _mission_or_404(db, mission_id)
    await ensure_mission_accessible(db, mission, user)

    attempt = await _locked_attempt(db, payload.attempt_id, user, mission_id)
    if attempt.module != "grammar":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "WRONG_ATTEMPT_MODULE", "message": "This attempt is not a grammar attempt"},
        )
    if attempt.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ATTEMPT_ALREADY_COMPLETED", "message": "This attempt was already submitted"},
        )

    progress = await _progress_or_none(db, user.id, mission_id)
    if progress is None or not progress.game_passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "GAME_REQUIRED", "message": "Pass the dictionary game before grammar"},
        )

    questions = await _mission_grammar_questions(db, mission_id)
    issued_ids = json.loads(attempt.issued or "[]")
    if not issued_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NO_GRAMMAR_QUESTIONS", "message": "This mission has no grammar questions"},
        )

    submitted = {answer.question_id: answer for answer in payload.answers}
    if set(submitted) != set(issued_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INCOMPLETE_ANSWERS", "message": "Answer every grammar question of the mission"},
        )

    correct = 0
    for question_id, answer in submitted.items():
        question = questions.get(question_id)
        if question is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_QUESTION", "message": "Question does not belong to this mission"},
            )
        option = next((o for o in question.options if o.id == answer.option_id), None)
        if option is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_OPTION", "message": "Option does not belong to the question"},
            )
        if option.is_correct:
            correct += 1

    percent = correct / len(issued_ids) * 100.0
    passed = percent >= settings.GAME_PASS_THRESHOLD
    completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        claim = await db.execute(
            update(MissionAttempt)
            .where(MissionAttempt.id == attempt.id, MissionAttempt.status == "in_progress")
            .values(
                status="completed" if passed else "failed",
                score=round(percent, 2),
                completed_at=completed_at,
            )
            .returning(MissionAttempt.id)
        )
        if claim.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ATTEMPT_ALREADY_COMPLETED", "message": "This attempt was already submitted"},
            )

        if not passed:
            await db.commit()
            return {
                "success": False,
                "passed": False,
                "percent": round(percent, 2),
                "xp_awarded": 0,
                "total_xp": user.total_xp,
                "mission_completed": bool(progress.is_completed),
            }

        completed_before = await db.scalar(
            select(func.count(MissionAttempt.id)).where(
                MissionAttempt.user_id == user.id,
                MissionAttempt.mission_id == mission_id,
                MissionAttempt.module == "grammar",
                MissionAttempt.status == "completed",
                MissionAttempt.id != attempt.id,
            )
        )
        first_time = int(completed_before or 0) == 0

        xp = await _xp_sum(
            db,
            mission_id,
            Task.xp_reward_first if first_time else Task.xp_reward_repeat,
            task_types=["grammar"],
        )

        best_score = max(progress.best_score_percentage or 0.0, percent)
        all_stages_done = bool(
            progress.tests_passed
            and progress.pronunciation_passed
            and progress.game_passed
        )
        already_completed = bool(progress.is_completed)
        mission_completed = already_completed or all_stages_done

        new_total = await db.scalar(
            update(User)
            .where(User.id == user.id)
            .values(total_xp=func.coalesce(User.total_xp, 0) + xp)
            .returning(User.total_xp)
            .execution_options(synchronize_session=False)
        )
        attempt.xp_earned = xp

        new_completion = await db.scalar(
            update(UserMissionProgress)
            .where(
                UserMissionProgress.user_id == user.id,
                UserMissionProgress.mission_id == mission_id,
            )
            .values(
                grammar_passed=True,
                is_completed=mission_completed,
                completion_count=func.coalesce(UserMissionProgress.completion_count, 0) + 1,
                best_score_percentage=best_score,
                xp_earned=func.coalesce(UserMissionProgress.xp_earned, 0) + xp,
                last_completed_at=completed_at,
            )
            .returning(UserMissionProgress.completion_count)
            .execution_options(synchronize_session=False)
        )

        await recompute_unlocked_rank(db, user)

        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise

    return {
        "success": True,
        "passed": True,
        "percent": round(percent, 2),
        "xp_awarded": xp,
        "total_xp": new_total,
        "mission_completed": mission_completed,
        "completion_count": new_completion,
    }


async def check_grammar_answer(db: AsyncSession, mission_id: int, user: User, payload) -> dict:
    """Reveal whether a single picked form is correct (instant game feedback).

    Answers are still re-graded server-side on submit; this endpoint only helps
    the UI react immediately and never returns the whole answer key.
    """
    mission = await _mission_or_404(db, mission_id)
    await ensure_mission_accessible(db, mission, user)

    questions = await _mission_grammar_questions(db, mission_id)
    question = questions.get(payload.question_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_QUESTION", "message": "Question does not belong to this mission"},
        )
    option = next((o for o in question.options if o.id == payload.option_id), None)
    if option is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_OPTION", "message": "Option does not belong to the question"},
        )
    return {"question_id": question.id, "option_id": option.id, "correct": bool(option.is_correct)}
