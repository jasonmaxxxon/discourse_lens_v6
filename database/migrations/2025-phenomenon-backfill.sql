-- Backfill phenomenon columns from analysis_json (one-time utility)
update public.threads_posts
set
    phenomenon_id = (analysis_json -> 'phenomenon' ->> 'id')::uuid,
    phenomenon_status = coalesce((analysis_json -> 'phenomenon' ->> 'status'), 'pending'),
    phenomenon_case_id = coalesce(phenomenon_case_id, analysis_json ->> 'phenomenon_case_id')
where phenomenon_id is null
  and analysis_json ? 'phenomenon'
  and (analysis_json -> 'phenomenon' ->> 'id') is not null;
