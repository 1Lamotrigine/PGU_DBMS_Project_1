from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.middleware.auth_middleware import get_current_user
from src.models.models import User
from src.services.account_service import (
    get_profile,
    list_calibration_questions,
    login_user,
    register_user,
)
from src.services.calibration_service import submit_calibration
from src.validators.auth_validator import (
    CalibrationSubmitRequest,
    LoginRequest,
    RegisterRequest,
)


async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> dict:
    return await register_user(db, payload)


async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    return await login_user(db, payload)


async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    return await get_profile(db, current_user.id)


async def calibration_submit(
    payload: CalibrationSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await submit_calibration(db, current_user, payload)


async def calibration_questions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await list_calibration_questions(db)
