-- CDX-065b: cluster tactics storage + index (idempotent)
alter table if exists public.threads_comment_clusters
  add column if not exists tactics text[],
  add column if not exists tactic_summary text;

create index if not exists idx_threads_comment_clusters_tactics_gin
  on public.threads_comment_clusters using gin (tactics);
