"""Lightweight startup migrations.

``Base.metadata.create_all`` creates missing *tables* but never alters existing
ones. This module adds columns introduced after a database was first created, so
an existing database keeps working after an upgrade without manual SQL.

Each step is idempotent and dialect-aware. It is intentionally small; a real
project should move to Alembic.
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger("english_quest")

# (table, column, DDL added to ALTER TABLE)
_ADDED_COLUMNS: list[tuple[str, str, str]] = [
    ("users", "unlocked_level_rank", "INTEGER NOT NULL DEFAULT 0"),
    ("user_mission_progress", "xp_earned", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "google_id", "VARCHAR(255)"),
    ("user_mission_progress", "game_passed", "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("user_mission_progress", "grammar_passed", "BOOLEAN NOT NULL DEFAULT FALSE"),
]

_BACKFILL = [
    # Trust the calibrated level as the initial unlocked level.
    """
    UPDATE users SET unlocked_level_rank = CASE cefr_level
        WHEN 'A1' THEN 0 WHEN 'A2' THEN 1 WHEN 'B1' THEN 2
        WHEN 'B2' THEN 3 WHEN 'C1' THEN 4 WHEN 'C2' THEN 5 ELSE 0 END
    WHERE unlocked_level_rank = 0
    """,
    # Missions completed before the grammar module existed have already had
    # their game stage passed; treat them as such so only grammar is missing.
    """
    UPDATE user_mission_progress SET game_passed = TRUE
    WHERE is_completed = TRUE AND game_passed = FALSE
    """,
]


async def run_startup_migrations(conn: AsyncConnection) -> None:
    existing_tables = set(await conn.run_sync(lambda c: inspect(c).get_table_names()))
    added_any = False

    for table, column, ddl in _ADDED_COLUMNS:
        if table not in existing_tables:
            continue  # create_all will build it with the column already
        columns = await conn.run_sync(lambda c, t=table: {col["name"] for col in inspect(c).get_columns(t)})
        if column in columns:
            continue
        logger.info("Adding column %s.%s", table, column)
        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
        added_any = True

    if added_any:
        for statement in _BACKFILL:
            await conn.execute(text(statement))

    if "users" in existing_tables:
        await _ensure_google_integration(conn)

    if conn.dialect.name == "postgresql":
        await _ensure_content_constraints(conn)


async def _ensure_content_constraints(conn: AsyncConnection) -> None:
    """Widen CHECK constraints for newer task/question/attempt kinds.

    ``create_all`` never alters existing CHECK constraints, so an older database
    would reject the grammar task without these idempotent redefinitions.
    """
    statements = [
        "ALTER TABLE tasks DROP CONSTRAINT IF EXISTS ck_tasks_task_type",
        "ALTER TABLE tasks ADD CONSTRAINT ck_tasks_task_type CHECK "
        "(task_type IN ('vocabulary_game','multiple_choice','translation','grammar'))",
        "ALTER TABLE questions DROP CONSTRAINT IF EXISTS ck_questions_question_type",
        "ALTER TABLE questions ADD CONSTRAINT ck_questions_question_type CHECK "
        "(question_type IN ('multiple_choice','fill_blank','translation','image_match','grammar_choice'))",
        "ALTER TABLE mission_attempts DROP CONSTRAINT IF EXISTS ck_attempt_module",
        "ALTER TABLE mission_attempts ADD CONSTRAINT ck_attempt_module CHECK "
        "(module IN ('test','pronunciation','game','grammar'))",
    ]
    for statement in statements:
        await conn.execute(text(statement))


async def _ensure_google_integration(conn: AsyncConnection) -> None:
    """Google Sign-In needs a unique google_id and a nullable password_hash."""
    # Older databases have password_hash NOT NULL; Google-only users have no
    # password, so the column must allow NULL. SQLite cannot ALTER this, but
    # create_all builds fresh SQLite databases with the right definition.
    if conn.dialect.name == "postgresql":
        columns = await conn.run_sync(
            lambda c: {col["name"]: col for col in inspect(c).get_columns("users")}
        )
        password_column = columns.get("password_hash")
        if password_column is not None and not password_column["nullable"]:
            logger.info("Allowing NULL in users.password_hash")
            await conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))

    # Multiple NULLs are allowed by a plain UNIQUE index, so password-only
    # accounts are unaffected.
    await conn.execute(
        text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)")
    )
