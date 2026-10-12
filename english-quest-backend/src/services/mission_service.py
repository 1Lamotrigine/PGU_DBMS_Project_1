from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.settings import settings
from src.models.models import (
    Level,
    Mission,
    Question,
    QuestionOption,
    Task,
    UserMissionProgress,
    VocabularyItem,
)
from src.services.access import ensure_mission_accessible, is_teacher


def _serialize_task(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "type": task.task_type,
        "description": task.description,
        "order_number": task.order_number,
        "time_limit": task.time_limit,
        "xp_reward_first": task.xp_reward_first,
        "xp_reward_repeat": task.xp_reward_repeat,
    }


def _serialize_mission(mission: Mission, locked: bool = False) -> dict:
    return {
        "id": mission.id,
        "level_id": mission.level_id,
        "order_index": mission.order_index,
        "title": mission.title,
        "description": mission.description,
        "is_active": mission.is_active,
        "locked": locked,
        "tasks": [_serialize_task(t) for t in mission.tasks],
    }


async def list_levels(db: AsyncSession, user) -> list[dict]:
    result = await db.execute(
        select(Level).options(selectinload(Level.missions).selectinload(Mission.tasks)).order_by(Level.id)
    )
    levels = list(result.scalars().all())

    progress_result = await db.execute(
        select(UserMissionProgress).where(UserMissionProgress.user_id == user.id)
    )
    progress_map = {p.mission_id: p for p in progress_result.scalars().all()}

    order = settings.CEFR_ORDER
    user_rank = order.index(user.cefr_level) if user.cefr_level in order else 0

    payload = []
    for level in levels:
        level_rank = order.index(level.code) if level.code in order else 0
        locked = level_rank > user_rank
        missions_payload = []
        for m in sorted(level.missions, key=lambda m: m.order_index):
            mission_payload = _serialize_mission(m, locked=locked)
            progress = progress_map.get(m.id)
            mission_payload["progress"] = {
                "is_completed": progress.is_completed if progress else False,
                "tests_passed": progress.tests_passed if progress else False,
                "pronunciation_passed": progress.pronunciation_passed if progress else False,
                "best_score_percentage": progress.best_score_percentage if progress else 0.0,
                "completion_count": progress.completion_count if progress else 0,
            }
            missions_payload.append(mission_payload)
        payload.append(
            {
                "id": level.id,
                "code": level.code,
                "title": level.title,
                "locked": locked,
                "missions": missions_payload,
            }
        )
    return payload


async def get_mission_detail(db: AsyncSession, mission_id: int, user) -> dict:
    result = await db.execute(
        select(Mission)
        .options(
            selectinload(Mission.tasks)
            .selectinload(Task.questions)
            .selectinload(Question.options)
        )
        .where(Mission.id == mission_id)
    )
    mission = result.scalar_one_or_none()
    if mission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Mission not found"},
        )

    await ensure_mission_accessible(db, mission, user)
    show_correct = is_teacher(user)

    progress_result = await db.execute(
        select(UserMissionProgress).where(
            UserMissionProgress.user_id == user.id,
            UserMissionProgress.mission_id == mission.id,
        )
    )
    progress = progress_result.scalar_one_or_none()

    tasks_payload = []
    for task in sorted(mission.tasks, key=lambda t: t.order_number):
        task_payload = _serialize_task(task)
        task_payload["questions"] = [
            {
                "id": question.id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "options": [
                    {
                        "id": option.id,
                        "option_text": option.option_text,
                        "translation_ru": option.translation_ru,
                        "image_url": option.image_url,
                        # Never expose the correct answer to students.
                        **({"is_correct": option.is_correct} if show_correct else {}),
                    }
                    for option in question.options
                ],
            }
            for question in task.questions
        ]
        tasks_payload.append(task_payload)

    return {
        "id": mission.id,
        "level_id": mission.level_id,
        "order_index": mission.order_index,
        "title": mission.title,
        "description": mission.description,
        "is_active": mission.is_active,
        "tasks": tasks_payload,
        "progress": {
            "is_completed": progress.is_completed if progress else False,
            "tests_passed": progress.tests_passed if progress else False,
            "pronunciation_passed": progress.pronunciation_passed if progress else False,
            "best_score_percentage": progress.best_score_percentage if progress else 0.0,
            "completion_count": progress.completion_count if progress else 0,
        },
    }


async def _reload_mission(db: AsyncSession, mission_id: int) -> dict:
    result = await db.execute(
        select(Mission).options(selectinload(Mission.tasks)).where(Mission.id == mission_id)
    )
    mission = result.scalar_one()
    return _serialize_mission(mission)


async def _mission_count(db: AsyncSession, level_id: int, exclude_mission_id: int | None = None) -> int:
    query = select(func.count(Mission.id)).where(Mission.level_id == level_id)
    if exclude_mission_id is not None:
        query = query.where(Mission.id != exclude_mission_id)
    result = await db.execute(query)
    return int(result.scalar_one())


async def _assert_publishable(db: AsyncSession, mission_id: int) -> None:
    """Content-readiness gate: don't publish a mission with broken questions."""
    result = await db.execute(
        select(Question)
        .join(Task, Question.task_id == Task.id)
        .options(selectinload(Question.options))
        .where(Task.mission_id == mission_id)
    )
    for question in result.scalars().all():
        if question.question_type != "multiple_choice":
            continue
        if len(question.options) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "QUESTION_INCOMPLETE",
                    "message": f"Question {question.id} needs at least two options",
                },
            )
        correct = [o for o in question.options if o.is_correct]
        if len(correct) != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "QUESTION_INCOMPLETE",
                    "message": f"Question {question.id} must have exactly one correct option",
                },
            )


async def create_mission(db: AsyncSession, payload) -> dict:
    level = await db.get(Level, payload.level_id)
    if level is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "LEVEL_NOT_FOUND", "message": "Level does not exist"},
        )
    if await _mission_count(db, payload.level_id) >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "LEVEL_FULL", "message": "A level cannot contain more than 5 missions"},
        )

    mission = Mission(
        level_id=payload.level_id,
        order_index=payload.order_index,
        title=payload.title,
        description=payload.description,
        is_active=payload.is_active,
    )
    for task_payload in payload.tasks:
        mission.tasks.append(
            Task(
                title=task_payload.title,
                description=task_payload.description,
                task_type=task_payload.task_type,
                order_number=task_payload.order_number,
                time_limit=task_payload.time_limit,
                xp_reward_first=task_payload.xp_reward_first,
                xp_reward_repeat=task_payload.xp_reward_repeat,
            )
        )
    db.add(mission)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "MISSION_CONFLICT",
                "message": "A mission with this level and order already exists",
            },
        )
    return await _reload_mission(db, mission.id)


async def update_mission(db: AsyncSession, mission_id: int, payload) -> dict:
    result = await db.execute(
        select(Mission).options(selectinload(Mission.tasks)).where(Mission.id == mission_id)
    )
    mission = result.scalar_one_or_none()
    if mission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Mission not found"},
        )

    data = payload.model_dump(exclude_unset=True)
    if data.get("level_id") is not None and await db.get(Level, data["level_id"]) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "LEVEL_NOT_FOUND", "message": "Level does not exist"},
        )
    for field, value in data.items():
        setattr(mission, field, value)

    if data.get("is_active") is True and mission.tasks:
        await _assert_publishable(db, mission_id)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "MISSION_CONFLICT",
                "message": "A mission with this level and order already exists",
            },
        )
    return await _reload_mission(db, mission.id)


async def delete_mission(db: AsyncSession, mission_id: int) -> dict:
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if mission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Mission not found"},
        )
    progress_count = await db.scalar(
        select(func.count(UserMissionProgress.id)).where(UserMissionProgress.mission_id == mission_id)
    )
    if int(progress_count or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "MISSION_IN_USE",
                "message": "Mission has user progress; archive it instead of deleting",
            },
        )
    await db.delete(mission)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "MISSION_IN_USE", "message": "Mission is referenced by other records"},
        )
    return {"deleted": True, "id": mission_id}


async def get_mission_vocabulary(db: AsyncSession, mission_id: int, user) -> list[dict]:
    """RU -> EN pairs for the Dictionary game of the mission's level."""
    result = await db.execute(select(Mission).where(Mission.id == mission_id))
    mission = result.scalar_one_or_none()
    if mission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Mission not found"},
        )

    await ensure_mission_accessible(db, mission, user)

    vocab_result = await db.execute(
        select(VocabularyItem).where(VocabularyItem.level_id == mission.level_id).order_by(VocabularyItem.id)
    )
    return [
        {
            "id": item.id,
            "word_en": item.word_en,
            "word_ru": item.word_ru,
            "transcription": item.transcription,
            "image_url": item.image_url,
        }
        for item in vocab_result.scalars().all()
    ]


async def list_recommended_missions(db: AsyncSession, user) -> list[dict]:
    """All missions of the user's level, in order, with completion status."""
    result = await db.execute(select(Level).where(Level.code == user.cefr_level))
    level = result.scalar_one_or_none()
    if level is None:
        return []

    missions_result = await db.execute(
        select(Mission)
        .options(selectinload(Mission.tasks))
        .where(Mission.level_id == level.id, Mission.is_active.is_(True))
        .order_by(Mission.order_index)
    )
    missions = list(missions_result.scalars().all())

    progress_result = await db.execute(
        select(UserMissionProgress).where(UserMissionProgress.user_id == user.id)
    )
    progress_map = {p.mission_id: p for p in progress_result.scalars().all()}

    recommended = []
    for mission in missions:
        progress = progress_map.get(mission.id)
        if progress and progress.is_completed:
            continue  # exclude already completed missions
        payload = _serialize_mission(mission)
        payload["is_completed"] = bool(progress and progress.is_completed)
        payload["progress"] = {
            "is_completed": progress.is_completed if progress else False,
            "tests_passed": progress.tests_passed if progress else False,
            "pronunciation_passed": progress.pronunciation_passed if progress else False,
            "best_score_percentage": progress.best_score_percentage if progress else 0.0,
            "completion_count": progress.completion_count if progress else 0,
        }
        recommended.append(payload)
    return recommended


# ---------------------------------------------------------------------------
# Task / Question / Option CRUD (teacher-managed content)
# ---------------------------------------------------------------------------
def _serialize_question(question: Question) -> dict:
    return {
        "id": question.id,
        "question_text": question.question_text,
        "question_type": question.question_type,
        "options": [
            {
                "id": o.id,
                "option_text": o.option_text,
                "translation_ru": o.translation_ru,
                "image_url": o.image_url,
                "is_correct": o.is_correct,
            }
            for o in question.options
        ],
    }


def _serialize_option(option: QuestionOption) -> dict:
    return {
        "id": option.id,
        "question_id": option.question_id,
        "option_text": option.option_text,
        "translation_ru": option.translation_ru,
        "image_url": option.image_url,
        "is_correct": option.is_correct,
    }


async def _get_or_404(db: AsyncSession, model, obj_id: int, name: str):
    result = await db.execute(select(model).where(model.id == obj_id))
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": f"{name} not found"},
        )
    return obj


async def _load_question(db: AsyncSession, question_id: int) -> Question:
    result = await db.execute(
        select(Question).options(selectinload(Question.options)).where(Question.id == question_id)
    )
    question = result.scalar_one_or_none()
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Question not found"},
        )
    return question


# ---- Tasks ----
async def create_task(db: AsyncSession, mission_id: int, payload) -> dict:
    await _get_or_404(db, Mission, mission_id, "Mission")
    task = Task(
        mission_id=mission_id,
        title=payload.title,
        description=payload.description,
        task_type=payload.task_type,
        order_number=payload.order_number,
        time_limit=payload.time_limit,
        xp_reward_first=payload.xp_reward_first,
        xp_reward_repeat=payload.xp_reward_repeat,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _serialize_task(task)


async def update_task(db: AsyncSession, task_id: int, payload) -> dict:
    task = await _get_or_404(db, Task, task_id, "Task")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return _serialize_task(task)


async def delete_task(db: AsyncSession, task_id: int) -> dict:
    task = await _get_or_404(db, Task, task_id, "Task")
    await db.delete(task)
    await db.commit()
    return {"deleted": True, "id": task_id}


# ---- Questions ----
async def create_question(db: AsyncSession, task_id: int, payload) -> dict:
    await _get_or_404(db, Task, task_id, "Task")
    question = Question(
        task_id=task_id,
        question_text=payload.question_text,
        question_type=payload.question_type,
    )
    db.add(question)
    await db.commit()
    return _serialize_question(await _load_question(db, question.id))


async def update_question(db: AsyncSession, question_id: int, payload) -> dict:
    question = await _get_or_404(db, Question, question_id, "Question")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(question, field, value)
    await db.commit()
    return _serialize_question(await _load_question(db, question_id))


async def delete_question(db: AsyncSession, question_id: int) -> dict:
    question = await _get_or_404(db, Question, question_id, "Question")
    await db.delete(question)
    await db.commit()
    return {"deleted": True, "id": question_id}


# ---- Options ----
async def create_option(db: AsyncSession, question_id: int, payload) -> dict:
    await _get_or_404(db, Question, question_id, "Question")
    option = QuestionOption(
        question_id=question_id,
        option_text=payload.option_text,
        is_correct=payload.is_correct,
        image_url=payload.image_url,
        translation_ru=payload.translation_ru,
    )
    db.add(option)
    await db.commit()
    await db.refresh(option)
    return _serialize_option(option)


async def update_option(db: AsyncSession, option_id: int, payload) -> dict:
    option = await _get_or_404(db, QuestionOption, option_id, "Option")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(option, field, value)
    await db.commit()
    await db.refresh(option)
    return _serialize_option(option)


async def delete_option(db: AsyncSession, option_id: int) -> dict:
    option = await _get_or_404(db, QuestionOption, option_id, "Option")
    await db.delete(option)
    await db.commit()
    return {"deleted": True, "id": option_id}


# ---- Vocabulary ----
def _serialize_vocab(item: VocabularyItem) -> dict:
    return {
        "id": item.id,
        "level_id": item.level_id,
        "word_en": item.word_en,
        "word_ru": item.word_ru,
        "transcription": item.transcription,
        "image_url": item.image_url,
    }


async def list_level_vocabulary(db: AsyncSession, level_id: int) -> list[dict]:
    await _get_or_404(db, Level, level_id, "Level")
    result = await db.execute(
        select(VocabularyItem).where(VocabularyItem.level_id == level_id).order_by(VocabularyItem.id)
    )
    return [_serialize_vocab(v) for v in result.scalars().all()]


async def create_vocabulary(db: AsyncSession, level_id: int, payload) -> dict:
    await _get_or_404(db, Level, level_id, "Level")
    item = VocabularyItem(
        level_id=level_id,
        word_en=payload.word_en,
        word_ru=payload.word_ru,
        transcription=payload.transcription,
        image_url=payload.image_url,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _serialize_vocab(item)


async def update_vocabulary(db: AsyncSession, vocab_id: int, payload) -> dict:
    item = await _get_or_404(db, VocabularyItem, vocab_id, "Vocabulary item")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return _serialize_vocab(item)

async def delete_vocabulary(db: AsyncSession, vocab_id: int) -> dict:
    item = await _get_or_404(db, VocabularyItem, vocab_id, "Vocabulary item")
    await db.delete(item)
    await db.commit()
    return {"deleted": True, "id": vocab_id}
