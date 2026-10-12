from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.middleware.auth_middleware import get_current_user
from src.models.models import User
from src.services.game_service import (
    start_attempt,
    submit_game,
    submit_pronunciation,
    submit_tests,
)
from src.validators.game_validator import (
    StartAttemptRequest,
    SubmitGameRequest,
    SubmitPronunciationRequest,
    SubmitTestsRequest,
)


async def start_mission_attempt(
    mission_id: int,
    payload: StartAttemptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await start_attempt(db, mission_id, current_user, payload.module)


async def submit_mission_tests(
    mission_id: int,
    payload: SubmitTestsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await submit_tests(db, mission_id, current_user, payload)


async def submit_mission_pronunciation(
    mission_id: int,
    payload: SubmitPronunciationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await submit_pronunciation(db, mission_id, current_user, payload)


async def submit_mission_game(
    mission_id: int,
    payload: SubmitGameRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await submit_game(db, mission_id, current_user, payload)
