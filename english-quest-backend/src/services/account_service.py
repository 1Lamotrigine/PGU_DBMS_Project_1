from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import Role, User
from src.services.security import create_access_token, hash_password, verify_password
from src.services.user_lookup import get_user_by_email, get_user_with_role


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.first_name,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "email": user.email,
        "role": user.role.name if user.role else None,
        "cefr_level": user.cefr_level,
        "total_xp": user.total_xp,
        "is_calibrated": user.is_calibrated,
    }


async def _default_student_role(db: AsyncSession) -> Role:
    result = await db.execute(select(Role).where(Role.name == "student"))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "ROLE_MISSING", "message": "Default role 'student' is not seeded"},
        )
    return role


async def register_user(db: AsyncSession, payload) -> dict:
    existing = await get_user_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMAIL_TAKEN", "message": "Email is already registered", "details": []},
        )

    role = await _default_student_role(db)
    user = User(
        first_name=payload.firstName,
        last_name=payload.lastName,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role_id=role.id,
    )
    db.add(user)
    await db.commit()

    user = await get_user_by_email(db, payload.email)
    token = create_access_token(user.id, role.name)
    return {"token": token, "user": serialize_user(user)}


async def login_user(db: AsyncSession, payload) -> dict:
    user = await get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password", "details": []},
        )

    token = create_access_token(user.id, user.role.name if user.role else "student")
    return {"token": token, "user": serialize_user(user)}


async def get_profile(db: AsyncSession, user_id: int) -> dict:
    user = await get_user_with_role(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "User not found"},
        )
    return serialize_user(user)


async def list_calibration_questions(db: AsyncSession) -> list[dict]:
    from src.models.models import CalibrationQuestion

    result = await db.execute(select(CalibrationQuestion).order_by(CalibrationQuestion.id))
    return [
        {
            "id": q.id,
            "question_text": q.question_text,
            "cefr_level": q.cefr_level,
            "options": {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d,
            },
        }
        for q in result.scalars().all()
    ]
