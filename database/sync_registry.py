import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any

from supabase import create_client


def load_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY not set")
    return create_client(url, key)


def fetch_post_phenomena(sb):
    resp = (
        sb.table("threads_posts")
        .select("phenomenon_id, phenomenon_case_id, created_at")
        .not_.is_("phenomenon_id", None)
        .execute()
    )
    rows = resp.data or []
    agg: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "case_ids": [], "latest_ts": None})
    for row in rows:
        pid = row.get("phenomenon_id")
        if not pid:
            continue
        agg[pid]["count"] += 1
        case_id = row.get("phenomenon_case_id")
        if case_id:
            agg[pid]["case_ids"].append(case_id)
        ts = row.get("created_at")
        if ts and (agg[pid]["latest_ts"] is None or ts > agg[pid]["latest_ts"]):
            agg[pid]["latest_ts"] = ts
    return agg


def fetch_existing_registry(sb):
    resp = sb.table("narrative_phenomena").select("id, status, canonical_name, description, created_at").execute()
    rows = resp.data or []
    return {row["id"]: row for row in rows if isinstance(row, dict) and row.get("id")}


def sync_registry():
    sb = load_supabase()
    post_map = fetch_post_phenomena(sb)
    if not post_map:
        print("No phenomenon_id found in threads_posts; nothing to sync.")
        return

    existing = fetch_existing_registry(sb)
    upserts = []
    for pid, info in post_map.items():
        row = existing.get(pid, {})
        status = row.get("status") or "provisional"
        minted_case = info["case_ids"][-1] if info["case_ids"] else None
        record = {
            "id": pid,
            "status": status,
            "occurrence_count": info["count"],
        }
        if minted_case:
            record["minted_by_case_id"] = minted_case
        if not row.get("created_at"):
            record["created_at"] = datetime.utcnow().isoformat()
        # preserve canonical_name/description by omitting them if already present
        if not row.get("canonical_name"):
            record["canonical_name"] = None
        if not row.get("description"):
            record["description"] = None
        upserts.append(record)

    if upserts:
        sb.table("narrative_phenomena").upsert(upserts).execute()
        print(f"Upserted {len(upserts)} registry rows.")

    # Verification
    refreshed = fetch_existing_registry(sb)
    missing = [pid for pid in post_map if pid not in refreshed]
    print(
        {
            "distinct_in_posts": len(post_map),
            "rows_in_registry": len(refreshed),
            "missing_after_sync": len(missing),
        }
    )
    if missing:
        print("Missing ids after sync:", missing)


if __name__ == "__main__":
    sync_registry()
