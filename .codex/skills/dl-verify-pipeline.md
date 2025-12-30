# dl-verify-pipeline

- **When to run**: After backend changes to Pipeline A or before merging to main.
- **Command**: `python .codex/tools/verify_pipeline.py <threads_url>`
- **Definition of Done**: Pipeline A job completes, returns a `post_id`, and analysis endpoint responds with `analysis_json` or `full_report` content.
