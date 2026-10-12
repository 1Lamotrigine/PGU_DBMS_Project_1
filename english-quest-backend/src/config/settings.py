from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_SECRET = "change-me-in-production-super-secret-key"
_PLACEHOLDER_TEACHER_PASSWORD = "Teacher123"


class Settings(BaseSettings):
    """Application settings loaded from the .env file."""

    # Environment: "development" | "production"
    APP_ENV: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/english_quest"

    # JWT
    JWT_SECRET: str = _PLACEHOLDER_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # CORS
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3001,http://127.0.0.1:3001,"
        "http://localhost:3002,http://127.0.0.1:3002"
    )
    # Dev convenience: allow any localhost / 127.0.0.1 port.
    # Ignored in production (see _validate_production).
    CORS_ORIGIN_REGEX: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    # Seed teacher account
    TEACHER_EMAIL: str = "teacher@englishquest.dev"
    TEACHER_PASSWORD: str = _PLACEHOLDER_TEACHER_PASSWORD
    TEACHER_FIRST_NAME: str = "Teacher"
    TEACHER_LAST_NAME: str = "Quest"

    # When false, only roles/levels are seeded; demo content and the teacher
    # account are skipped (useful for production).
    SEED_DEMO: bool = True

    # Game rules
    GAME_PASS_THRESHOLD: float = 70.0

    # Simple in-process rate limiting (requests per window per client IP).
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_DEFAULT: int = 240
    RATE_LIMIT_LOGIN: int = 10

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
    def is_production(self) -> bool:
        return self.APP_ENV.strip().lower() in ("production", "prod")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        """Refuse to start with placeholder secrets in production."""
        if not self.is_production:
            return self
        if self.JWT_SECRET == _PLACEHOLDER_SECRET or len(self.JWT_SECRET) < 32:
            raise ValueError(
                "JWT_SECRET must be set to a strong value (>=32 chars) when APP_ENV=production"
            )
        if self.TEACHER_PASSWORD == _PLACEHOLDER_TEACHER_PASSWORD or len(self.TEACHER_PASSWORD) < 12:
            raise ValueError(
                "TEACHER_PASSWORD must be changed (>=12 chars) when APP_ENV=production"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
