-- Threads comments structured table (raw evidence SoT)
create extension if not exists vector;

create table if not exists public.threads_comments (
  id text primary key,
  post_id bigint not null references public.threads_posts(id) on delete cascade,
  text text,
  author_handle text,
  like_count int,
  reply_count int,
  created_at timestamptz,
  captured_at timestamptz default now(),
  source_comment_id text,
  parent_comment_id text,
  author_id text,
  raw_json jsonb,
  cluster_label text,
  tactic_tag text,
  embedding vector(1536),
  inserted_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_threads_comments_post_id on public.threads_comments(post_id);
create index if not exists idx_threads_comments_author on public.threads_comments(author_handle);
create index if not exists idx_threads_comments_created_at on public.threads_comments(created_at);

-- Safe alters for existing tables
alter table if exists public.threads_comments
  add column if not exists captured_at timestamptz default now(),
  add column if not exists source_comment_id text,
  add column if not exists parent_comment_id text,
  add column if not exists author_id text;

create index if not exists idx_threads_comments_source_comment_id on public.threads_comments(source_comment_id);
create index if not exists idx_threads_comments_parent_comment_id on public.threads_comments(parent_comment_id);
