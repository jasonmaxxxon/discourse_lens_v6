-- CDX-068-G: Introduce Google text-embedding-004 (768-d) storage.
-- Safe approach: add new column + index + RPC; keep legacy embedding column intact.
-- Rollback: drop embedding_v768, drop index, drop match_phenomena_v768 (if created); legacy embedding untouched.

create extension if not exists vector;

alter table if exists public.narrative_phenomena
  add column if not exists embedding_v768 vector(768);

create index if not exists idx_narrative_phenomena_embedding_v768
  on public.narrative_phenomena using ivfflat (embedding_v768 vector_cosine_ops);

-- New RPC for 768-d embeddings; legacy match_phenomena (1536-d) retained.
create or replace function match_phenomena_v768 (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  canonical_name text,
  description text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    p.id,
    p.canonical_name,
    p.description,
    1 - (p.embedding_v768 <=> query_embedding) as similarity
  from narrative_phenomena p
  where p.embedding_v768 is not null
    and 1 - (p.embedding_v768 <=> query_embedding) > match_threshold
  order by p.embedding_v768 <=> query_embedding
  limit match_count;
end;
$$;

-- Notify PostgREST to reload schema
notify pgrst, 'reload schema';
