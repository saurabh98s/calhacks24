-- Migration 001: Per-Room Usernames
-- This migration removes the global unique constraint on usernames
-- and adds support for same username in different rooms

-- Step 1: Add current_room_id column if it doesn't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_room_id VARCHAR(100);

-- Step 2: Create index on current_room_id
CREATE INDEX IF NOT EXISTS ix_users_current_room_id ON users(current_room_id);

-- Step 3: Drop the global unique constraint on username
ALTER TABLE users DROP CONSTRAINT IF EXISTS ix_users_username;
DROP INDEX IF EXISTS ix_users_username;

-- Step 4: Add composite unique constraint: username + current_room_id
CREATE UNIQUE INDEX IF NOT EXISTS uix_username_room ON users(username, current_room_id);

-- Step 5: Create composite index for queries
CREATE INDEX IF NOT EXISTS ix_username_room ON users(username, current_room_id);

-- NOTE: This migration is handled automatically by SQLAlchemy's create_all()
-- This file is for reference only. To apply to existing database, run:
-- psql -U your_user -d your_database -f migration_001_per_room_usernames.sql

