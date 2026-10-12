from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.middleware.auth_middleware import get_current_user
from src.models.models import User
from src.services.mission_service import (
    create_mission,
    create_option,
    create_question,
    create_task,
    create_vocabulary,
    delete_mission,
    delete_option,
    delete_question,
    delete_task,
    delete_vocabulary,
    get_mission_detail,
    get_mission_vocabulary,
    list_level_vocabulary,
    list_levels,
    list_recommended_missions,
    update_mission,
    update_option,
    update_question,
    update_task,
    update_vocabulary,
)
from src.validators.mission_validator import (
    MissionCreate,
    MissionUpdate,
    OptionCreate,
    OptionUpdate,
    QuestionCreate,
    QuestionUpdate,
    TaskCreate,
    TaskUpdate,
    VocabularyCreate,
    VocabularyUpdate,
)


async def levels(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await list_levels(db, current_user)


async def mission_detail(
    mission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await get_mission_detail(db, mission_id, current_user)


async def mission_vocabulary(
    mission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await get_mission_vocabulary(db, mission_id, current_user)


async def recommended_missions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await list_recommended_missions(db, current_user)


async def mission_create(payload: MissionCreate, db: AsyncSession = Depends(get_db)) -> dict:
    return await create_mission(db, payload)


async def mission_update(
    mission_id: int,
    payload: MissionUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await update_mission(db, mission_id, payload)


async def mission_delete(mission_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    return await delete_mission(db, mission_id)


# ---- Tasks ----
async def task_create(mission_id: int, payload: TaskCreate, db: AsyncSession = Depends(get_db)) -> dict:
    return await create_task(db, mission_id, payload)


async def task_update(task_id: int, payload: TaskUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    return await update_task(db, task_id, payload)


async def task_delete(task_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    return await delete_task(db, task_id)


# ---- Questions ----
async def question_create(task_id: int, payload: QuestionCreate, db: AsyncSession = Depends(get_db)) -> dict:
    return await create_question(db, task_id, payload)


async def question_update(question_id: int, payload: QuestionUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    return await update_question(db, question_id, payload)


async def question_delete(question_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    return await delete_question(db, question_id)


# ---- Options ----
async def option_create(question_id: int, payload: OptionCreate, db: AsyncSession = Depends(get_db)) -> dict:
    return await create_option(db, question_id, payload)


async def option_update(option_id: int, payload: OptionUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    return await update_option(db, option_id, payload)


async def option_delete(option_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    return await delete_option(db, option_id)


# ---- Vocabulary ----
async def level_vocabulary_list(level_id: int, db: AsyncSession = Depends(get_db)) -> list[dict]:
    return await list_level_vocabulary(db, level_id)


async def vocabulary_create(level_id: int, payload: VocabularyCreate, db: AsyncSession = Depends(get_db)) -> dict:
    return await create_vocabulary(db, level_id, payload)


async def vocabulary_update(vocab_id: int, payload: VocabularyUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    return await update_vocabulary(db, vocab_id, payload)


async def vocabulary_delete(vocab_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    return await delete_vocabulary(db, vocab_id)
