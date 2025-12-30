"""
Best-effort backfill for legacy comment rows missing source_comment_id.
Usage:
  python database/backfill_comment_source_ids.py --limit 200
Does not modify primary key (id); only sets source_comment_id when discoverable.
"""

import argparse
import json
import re
from typing import Any, Dict, Optional

from database.store import supabase  # reuse configured client/env

COMMENT_ID_KEYS = ["source_comment_id", "comment_id", "id", "pk", "feedback_id", "media_id", "thread_id"]
COMMENT_ID_PATTERNS = [
    re.compile(r'"comment_id"\s*:\s*"([^"]+)"'),
    re.compile(r'"source_comment_id"\s*:\s*"([^"]+)"'),
    re.compile(r'"id"\s*:\s*"([^"]+)"'),
    re.compile(r'"pk"\s*:\s*"([^"]+)"'),
    re.compile(r'"feedback_id"\s*:\s*"([^"]+)"'),
    re.compile(r'"media_id"\s*:\s*"([^"]+)"'),
    re.compile(r'"thread_id"\s*:\s*"([^"]+)"'),
]


def extract_id_from_raw(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    if isinstance(raw, dict):
        for key in COMMENT_ID_KEYS:
            val = raw.get(key)
            if val:
                return str(val)
        try:
            blob = json.dumps(raw)
        except Exception:
            blob = ""
    elif isinstance(raw, str):
        blob = raw
    else:
        blob = str(raw)

    for pattern in COMMENT_ID_PATTERNS:
        m = pattern.search(blob)
        if m:
            return m.group(1)
    return None


def backfill(limit: int = 200):
    resp = supabase.table("threads_comments").select("id, post_id, raw_json").is_("source_comment_id", None).limit(limit).execute()
    rows = getattr(resp, "data", None) or []
    if not rows:
        print("No rows missing source_comment_id.")
        return

    updated = 0
    for row in rows:
        raw = row.get("raw_json")
        candidate = extract_id_from_raw(raw)
        if not candidate:
            continue
        try:
            supabase.table("threads_comments").update({"source_comment_id": candidate}).eq("post_id", row.get("post_id")).eq("id", row.get("id")).execute()
            updated += 1
        except Exception as e:
            print(f"Failed to update row {row.get('id')}: {e}")
    print(f"Backfill complete. updated={updated}/{len(rows)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=200, help="max rows to attempt backfill for")
    args = parser.parse_args()
    backfill(limit=args.limit)
