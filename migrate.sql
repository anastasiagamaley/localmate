-- Migration: add deleted_at and welcome_tokens_granted to users table
-- Run this if you have existing data and don't want to wipe the DB

ALTER TABLE users 
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS welcome_tokens_granted BOOLEAN DEFAULT FALSE;

-- Mark all existing users as already having received welcome tokens
UPDATE users SET welcome_tokens_granted = TRUE WHERE welcome_tokens_granted IS NULL;
