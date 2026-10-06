from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from the .env file."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://niaz:niaz1997@localhost:5432/english_quest"

    # JWT
    JWT_SECRET: str = "change-me-in-production-super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # CORS
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3001,http://127.0.0.1:3001,"
        "http://localhost:3002,http://127.0.0.1:3002"
    )
    # Dev convenience: allow any localhost / 127.0.0.1 port.
    CORS_ORIGIN_REGEX: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    # Seed teacher account
    TEACHER_EMAIL: str = "teacher@englishquest.dev"
    TEACHER_PASSWORD: str = "Teacher123"
    TEACHER_FIRST_NAME: str = "Teacher"
    TEACHER_LAST_NAME: str = "Quest"

    # Game rules
    GAME_PASS_THRESHOLD: float = 70.0

    # Placement test thresholds -> CEFR level
    CALIBRATION_THRESHOLDS: dict = {
        "A1": 0.0,
        "A2": 60.0,
        "B1": 70.0,
        "B2": 80.0,
        "C1": 90.0,
        "C2": 100.0,
    }

    CEFR_ORDER: list = ["A1", "A2", "B1", "B2", "C1", "C2"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
