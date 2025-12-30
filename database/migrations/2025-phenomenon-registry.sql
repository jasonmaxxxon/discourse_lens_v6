-- CDX-044.3/056/057 Phenomenon Registry (Deterministic, governed)
-- Enable pgvector before any table uses vector type
create extension if not exists vector;
create extension if not exists "uuid-ossp";

create table if not exists narrative_phenomena (
    id uuid primary key,
    canonical_name text,
    description text,
    embedding vector(1536),
    status text default 'PROVISIONAL', -- PROVISIONAL | ACTIVE | DEPRECATED | MERGED
    minted_by_case_id uuid,
    occurrence_count int default 1,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists narrative_phenomenon_aliases (
    id uuid primary key default uuid_generate_v4(),
    phenomenon_id uuid references narrative_phenomena(id),
    alias_text text not null,
    language varchar(10),
    unique(alias_text, language)
);

create table if not exists narrative_phenomenon_relations (
    from_id uuid references narrative_phenomena(id),
    to_id uuid references narrative_phenomena(id),
    relation_type text, -- MERGED_INTO | SUB_TYPE_OF | RELATED
    created_at timestamptz default now()
);

-- Optional FK reference from analysis table (threads_posts) into registry.
-- This column is JSON-safe for backward compatibility.
alter table if exists threads_posts
    add column if not exists phenomenon_id uuid;

-- Safe alters for registry
alter table if exists narrative_phenomena
    add column if not exists canonical_name text,
    add column if not exists description text,
    add column if not exists embedding vector(1536),
    add column if not exists status text default 'PROVISIONAL',
    add column if not exists minted_by_case_id uuid,
    add column if not exists occurrence_count int default 1,
    add column if not exists updated_at timestamptz default now();

create index if not exists idx_narrative_phenomena_status on narrative_phenomena(status);
create index if not exists idx_narrative_phenomena_created_at on narrative_phenomena(created_at);
create index if not exists idx_narrative_phenomena_embedding on narrative_phenomena using ivfflat (embedding vector_cosine_ops);

-- Vector similarity helper for future match-or-mint
create or replace function match_phenomena (
  query_embedding vector(1536),
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
    1 - (p.embedding <=> query_embedding) as similarity
  from narrative_phenomena p
  where 1 - (p.embedding <=> query_embedding) > match_threshold
  order by p.embedding <=> query_embedding
  limit match_count;
end;
$$;
