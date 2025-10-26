-- Migration 002: Add persona column to users table
-- Run this with: psql -U postgres -d chatrealm -f backend/app/core/migration_002_add_persona.sql

-- Add persona column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS persona VARCHAR(1000);

-- Add comment
COMMENT ON COLUMN users.persona IS 'LinkedIn-generated user persona for AI context';

