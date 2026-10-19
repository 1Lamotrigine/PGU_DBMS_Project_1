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
]

_BACKFILL = [
    # Trust the calibrated level as the initial unlocked level.
    """
    UPDATE users SET unlocked_level_rank = CASE cefr_level
        WHEN 'A1' THEN 0 WHEN 'A2' THEN 1 WHEN 'B1' THEN 2
        WHEN 'B2' THEN 3 WHEN 'C1' THEN 4 WHEN 'C2' THEN 5 ELSE 0 END
    WHERE unlocked_level_rank = 0
    """
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
