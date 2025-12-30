-- Optional RPC to increment occurrence_count safely
create or replace function increment_occurrence(phenomenon_uuid uuid)
returns void
language plpgsql
as $$
begin
  update narrative_phenomena
  set occurrence_count = coalesce(occurrence_count, 0) + 1,
      updated_at = now()
  where id = phenomenon_uuid;
end;
$$;
