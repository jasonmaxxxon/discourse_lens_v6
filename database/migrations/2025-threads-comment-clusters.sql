-- Cluster registry and comment-cluster linking
create extension if not exists vector;
create extension if not exists pg_trgm;

create table if not exists public.threads_comment_clusters (
  id text primary key,
  post_id bigint not null references public.threads_posts(id) on delete cascade,
  cluster_key int,
  label text,
  summary text,
  size int,
  top_comment_ids jsonb,
  centroid_embedding vector(1536),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create unique index if not exists idx_comment_clusters_post_key on public.threads_comment_clusters(post_id, cluster_key);
create index if not exists idx_comment_clusters_post on public.threads_comment_clusters(post_id);
create index if not exists idx_comment_clusters_label_trgm on public.threads_comment_clusters using gin (label gin_trgm_ops);
create index if not exists idx_comment_clusters_embedding on public.threads_comment_clusters using ivfflat (centroid_embedding vector_cosine_ops);

-- add columns to threads_comments for cluster linking
alter table if exists public.threads_comments
  add column if not exists cluster_id text,
  add column if not exists cluster_key int;

-- best-effort FK (may require cleaning legacy data)
alter table if exists public.threads_comments
  add constraint if not exists threads_comments_cluster_fk foreign key (cluster_id) references public.threads_comment_clusters(id) on delete set null;

create index if not exists idx_threads_comments_cluster_id on public.threads_comments(cluster_id);
create index if not exists idx_threads_comments_post_cluster on public.threads_comments(post_id, cluster_key);
