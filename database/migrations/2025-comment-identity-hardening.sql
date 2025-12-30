-- CDX-064: Hybrid comment identity (native id in source_comment_id, hash id remains PK)
alter table if exists public.threads_comments
  add column if not exists source_comment_id text,
  add column if not exists parent_source_comment_id text;

create unique index if not exists idx_threads_comments_post_source_unique
  on public.threads_comments(post_id, source_comment_id)
  where source_comment_id is not null;

create index if not exists idx_threads_comments_source_id
  on public.threads_comments(source_comment_id)
  where source_comment_id is not null;

create index if not exists idx_threads_comments_parent_source_id
  on public.threads_comments(parent_source_comment_id)
  where parent_source_comment_id is not null;

-- refresh PGRST schema cache
notify pgrst, 'reload schema';
