-- Enrichment process observability
alter table public.threads_posts
  add column if not exists enrichment_status text default 'idle',
  add column if not exists enrichment_last_error text,
  add column if not exists enrichment_retry_count int default 0,
  add column if not exists enrichment_queued_at timestamptz,
  add column if not exists enrichment_started_at timestamptz,
  add column if not exists enrichment_completed_at timestamptz;

create index if not exists idx_threads_posts_analysis_segments
  on public.threads_posts
  using gin ((analysis_json->'segments'));

create index if not exists idx_threads_posts_enrichment_status
  on public.threads_posts (enrichment_status);

create index if not exists idx_threads_posts_enrichment_started_at
  on public.threads_posts (enrichment_started_at);
