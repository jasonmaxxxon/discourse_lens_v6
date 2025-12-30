# dl-db-json-safety

- **When to run**: Before committing any change that writes to Supabase (insert/update/upsert).
- **Command**: `python .codex/tools/lint_db_safety.py`
- **Rule**: All Supabase payloads must be JSON-safe (e.g., datetime/date converted via `jsonable_encoder` or `_json_safe`).
