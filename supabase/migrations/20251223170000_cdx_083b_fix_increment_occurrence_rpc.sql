-- CDX-083b: increment_occurrence RPC for narrative_phenomena

-- 1) Ensure column exists and is NOT NULL with DEFAULT 0 (backfill nulls)
ALTER TABLE public.narrative_phenomena
ADD COLUMN IF NOT EXISTS occurrence_count integer;

UPDATE public.narrative_phenomena
SET occurrence_count = 0
WHERE occurrence_count IS NULL;

ALTER TABLE public.narrative_phenomena
ALTER COLUMN occurrence_count SET DEFAULT 0;

ALTER TABLE public.narrative_phenomena
ALTER COLUMN occurrence_count SET NOT NULL;

-- 2) Create RPC function: returns updated count
DO $$
BEGIN
  -- drop incompatible prior definition (cannot alter return type)
  IF EXISTS (
    SELECT 1
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.proname = 'increment_occurrence'
      AND pg_catalog.pg_function_is_visible(p.oid)
  ) THEN
    DROP FUNCTION IF EXISTS public.increment_occurrence(uuid);
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION public.increment_occurrence(phenomenon_id uuid)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  new_count integer;
BEGIN
  UPDATE public.narrative_phenomena
  SET occurrence_count = occurrence_count + 1,
      updated_at = now()
  WHERE id = phenomenon_id
  RETURNING occurrence_count INTO new_count;

  RETURN new_count;
END;
$$;

-- 3) Grants for Supabase RPC usage
GRANT EXECUTE ON FUNCTION public.increment_occurrence(uuid) TO anon;
GRANT EXECUTE ON FUNCTION public.increment_occurrence(uuid) TO authenticated;
