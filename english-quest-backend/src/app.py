from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.database import Base, AsyncSessionLocal, engine
from src.config.settings import settings
from src.middleware.error_middleware import register_exception_handlers
from src.middleware.security_middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from src.routes.auth_routes import calibration_router, router as auth_router
from src.routes.game_routes import router as game_router
from src.routes.mission_routes import levels_router, vocabulary_router, router as mission_router
from src.routes.user_routes import router as user_router, students_router

# Import models so SQLAlchemy registers all tables before create_all.
from src.models import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from src.db.seed import seed

    async with AsyncSessionLocal() as session:
        await seed(session)

    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="English Quest API",
        version="1.0.0",
        description="Gamified English learning platform — Block 1 backend",
        lifespan=lifespan,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        # Never allow the permissive localhost regex in production.
        allow_origin_regex=None if settings.is_production else settings.CORS_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(calibration_router, prefix=api_prefix)
    app.include_router(levels_router, prefix=api_prefix)
    app.include_router(mission_router, prefix=api_prefix)
    app.include_router(vocabulary_router, prefix=api_prefix)
    app.include_router(game_router, prefix=api_prefix)
    app.include_router(user_router, prefix=api_prefix)
    app.include_router(students_router, prefix=api_prefix)

    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
