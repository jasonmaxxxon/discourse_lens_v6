alter table public.threads_comments
add column if not exists from_top_snapshot boolean not null default false;