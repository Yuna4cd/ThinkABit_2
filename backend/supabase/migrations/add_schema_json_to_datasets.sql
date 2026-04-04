-- Persist inferred dataset schema for GET /datasets/{dataset_id}/schema
-- Safe to run in Supabase SQL Editor.

ALTER TABLE IF EXISTS public.datasets
    ADD COLUMN IF NOT EXISTS schema_json jsonb NOT NULL DEFAULT '[]'::jsonb;
