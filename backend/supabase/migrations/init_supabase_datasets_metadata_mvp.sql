-- Supabase datasets metadata table (MVP)
-- Safe to run in Supabase SQL Editor.

-- 1) Enum type for parse status
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'dataset_parse_status'
          AND n.nspname = 'public'
    ) THEN
        CREATE TYPE public.dataset_parse_status AS ENUM (
            'uploaded',
            'parsing',
            'ready',
            'failed'
        );
    END IF;
END $$;

-- 2) Metadata table (MVP contract)
CREATE TABLE IF NOT EXISTS public.datasets (
    dataset_id text PRIMARY KEY,
    parse_status public.dataset_parse_status NOT NULL DEFAULT 'uploaded',
    original_filename text NOT NULL,
    extension text NOT NULL,
    mime_type text NOT NULL,
    size_bytes bigint NOT NULL,
    storage_key_raw text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT datasets_dataset_id_prefix_chk CHECK (dataset_id LIKE 'ds_%'),
    CONSTRAINT datasets_size_bytes_nonnegative_chk CHECK (size_bytes >= 0)
);

-- 3) Keep updated_at current on every update
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_datasets_set_updated_at ON public.datasets;

CREATE TRIGGER trg_datasets_set_updated_at
BEFORE UPDATE ON public.datasets
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();
