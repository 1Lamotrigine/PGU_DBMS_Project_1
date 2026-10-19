-- Migration: level/mission progression (unlocked level + per-mission XP).
-- Run this once against an existing database created before these columns were
-- added. Fresh databases created by create_all already include them.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS unlocked_level_rank INTEGER NOT NULL DEFAULT 0;

ALTER TABLE user_mission_progress
    ADD COLUMN IF NOT EXISTS xp_earned INTEGER NOT NULL DEFAULT 0;

-- Backfill: trust the calibrated level as the initial unlocked level.
UPDATE users
SET unlocked_level_rank = CASE cefr_level
    WHEN 'A1' THEN 0
    WHEN 'A2' THEN 1
    WHEN 'B1' THEN 2
    WHEN 'B2' THEN 3
    WHEN 'C1' THEN 4
    WHEN 'C2' THEN 5
    ELSE 0
END
WHERE unlocked_level_rank = 0;
