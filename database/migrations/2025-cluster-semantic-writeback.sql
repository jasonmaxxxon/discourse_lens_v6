-- CDX-065c: Ensure semantic writeback columns + indexes exist
alter table if exists public.threads_comment_clusters
  add column if not exists label text,
  add column if not exists summary text,
  add column if not exists tactics text[],
  add column if not exists tactic_summary text;

create index if not exists idx_threads_comment_clusters_tactics_gin
  on public.threads_comment_clusters using gin (tactics);

create unique index if not exists uq_threads_comment_clusters_post_key
  on public.threads_comment_clusters(post_id, cluster_key);

-- refresh PostgREST schema cache
notify pgrst, 'reload schema';
