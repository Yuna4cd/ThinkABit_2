-- Extend datasets metadata for dataset GET response contract
-- Safe to run in Supabase SQL Editor.

ALTER TABLE IF EXISTS public.datasets
    ADD COLUMN IF NOT EXISTS session_id text,
    ADD COLUMN IF NOT EXISTS row_count integer,
    ADD COLUMN IF NOT EXISTS column_count integer;
