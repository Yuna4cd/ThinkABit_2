-- Datasets metadata MVP verification checklist SQL

-- A) table and column existence
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'datasets'
ORDER BY ordinal_position;

-- B) enum values
SELECT
    t.typname AS enum_name,
    e.enumsortorder,
    e.enumlabel
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
JOIN pg_namespace n ON n.oid = t.typnamespace
WHERE n.nspname = 'public'
  AND t.typname = 'dataset_parse_status'
ORDER BY e.enumsortorder;

-- C) constraints
SELECT conname, pg_get_constraintdef(c.oid) AS definition
FROM pg_constraint c
JOIN pg_class r ON r.oid = c.conrelid
JOIN pg_namespace n ON n.oid = r.relnamespace
WHERE n.nspname = 'public'
  AND r.relname = 'datasets'
ORDER BY conname;

-- D) trigger existence
SELECT trigger_name, event_manipulation, action_timing
FROM information_schema.triggers
WHERE event_object_schema = 'public'
  AND event_object_table = 'datasets'
ORDER BY trigger_name;

-- E) behavior test (manual): default status + updated_at auto-update
-- Run these commands one by one in Supabase SQL editor.

-- 1) Insert row (parse_status omitted -> default 'uploaded')
INSERT INTO public.datasets (
    dataset_id,
    original_filename,
    extension,
    mime_type,
    size_bytes,
    storage_key_raw
)
VALUES (
    'ds_metadata_demo_001',
    'demo.csv',
    'csv',
    'text/csv',
    42,
    'raw/2026/03/19/ds_metadata_demo_001/demo.csv'
)
ON CONFLICT (dataset_id) DO NOTHING;

-- 2) Confirm default status and timestamps
SELECT dataset_id, parse_status, created_at, updated_at
FROM public.datasets
WHERE dataset_id = 'ds_metadata_demo_001';

-- 3) Trigger update and confirm updated_at changes
UPDATE public.datasets
SET original_filename = 'demo_v2.csv'
WHERE dataset_id = 'ds_metadata_demo_001';

SELECT dataset_id, original_filename, created_at, updated_at
FROM public.datasets
WHERE dataset_id = 'ds_metadata_demo_001';

-- 4) Clean up demo row (optional)
DELETE FROM public.datasets
WHERE dataset_id = 'ds_metadata_demo_001';
