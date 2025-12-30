-- CDX-083a: Ensure occurrence counter + RPC for narrative_phenomena

-- A) Column safety
ALTER TABLE public.narrative_phenomena
    ADD COLUMN IF NOT EXISTS occurrence_count integer NOT NULL DEFAULT 0;

-- Backfill any nulls (idempotent)
UPDATE public.narrative_phenomena
SET occurrence_count = 0
WHERE occurrence_count IS NULL;

-- B) RPC function
CREATE OR REPLACE FUNCTION public.increment_occurrence(phenomenon_id uuid)
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    new_count integer;
BEGIN
    UPDATE public.narrative_phenomena
    SET occurrence_count = COALESCE(occurrence_count, 0) + 1,
        updated_at = NOW()
    WHERE id = phenomenon_id
    RETURNING occurrence_count INTO new_count;

    RETURN COALESCE(new_count, 0);
END;
$$;

-- Ensure deterministic search_path
ALTER FUNCTION public.increment_occurrence(uuid) SET search_path = public;

-- Grants for API roles
GRANT EXECUTE ON FUNCTION public.increment_occurrence(uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION public.increment_occurrence(uuid) TO anon;
