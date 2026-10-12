import re

from pydantic import BaseModel, EmailStr, Field, field_validator

# bcrypt only consumes the first 72 bytes of a password. Reject anything longer
# so distinct passwords can never collapse to the same hash.
_BCRYPT_MAX_BYTES = 72


class RegisterRequest(BaseModel):
    firstName: str = Field(min_length=1, max_length=100)
    lastName: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("firstName", "lastName")
    @classmethod
    def strip_names(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name must not be blank")
        return value

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if len(value.encode("utf-8")) > _BCRYPT_MAX_BYTES:
            raise ValueError("Password is too long (max 72 bytes in UTF-8)")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class CalibrationAnswer(BaseModel):
    question_id: int = Field(gt=0)
    selected_option: str = Field(pattern="^[A-D]$")


class CalibrationSubmitRequest(BaseModel):
    answers: list[CalibrationAnswer] = Field(min_length=1)

    @field_validator("answers")
    @classmethod
    def unique_questions(cls, value: list[CalibrationAnswer]) -> list[CalibrationAnswer]:
        ids = [answer.question_id for answer in value]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate question_id in answers")
        return value
