import argparse
import hashlib
import os
from typing import Any, Dict, List

from supabase import create_client


def load_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY not set")
    return create_client(url, key)


def fallback_comment_id(post_id: str, comment: Dict[str, Any]) -> str:
    author = str(comment.get("author") or comment.get("user") or comment.get("author_handle") or "")
    text = str(comment.get("text") or "")
    created = str(comment.get("created_at") or comment.get("timestamp") or "")
    raw = f"{post_id}|{author}|{text}|{created}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def map_comments(comments: List[Dict[str, Any]], post_id: str) -> List[Dict[str, Any]]:
    rows = []
    for c in comments:
        if not isinstance(c, dict):
            continue
        cid = c.get("id") or c.get("comment_id") or fallback_comment_id(post_id, c)
        rows.append(
            {
                "id": str(cid),
                "post_id": str(post_id),
                "text": c.get("text"),
                "author_handle": c.get("author_handle") or c.get("user") or c.get("author"),
                "like_count": c.get("like_count") or c.get("likes"),
                "reply_count": c.get("reply_count") or c.get("replies"),
                "created_at": c.get("created_at") or c.get("timestamp"),
                "raw_json": c,
            }
        )
    return rows


def backfill(limit: int, since: str | None, target_post_id: str | None, dry_run: bool):
    sb = load_supabase()
    query = sb.table("threads_posts").select("id, raw_comments")
    if target_post_id:
        query = query.eq("id", target_post_id)
    if since:
        query = query.gte("created_at", since)
    if limit:
        query = query.limit(limit)
    resp = query.execute()
    posts = resp.data or []

    processed_posts = 0
    inserted = 0
    for row in posts:
        processed_posts += 1
        post_id = row.get("id")
        comments = row.get("raw_comments") or []
        if not post_id or not isinstance(comments, list):
            continue
        rows = map_comments(comments, post_id)
        inserted += len(rows)
        if not dry_run and rows:
            sb.table("threads_comments").upsert(rows).execute()

    return {"processed_posts": processed_posts, "inserted_comments": inserted, "dry_run": dry_run}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill threads_comments from threads_posts.raw_comments")
    parser.add_argument("--limit", type=int, default=500, help="Max posts to process")
    parser.add_argument("--since", type=str, default=None, help="ISO timestamp filter on created_at")
    parser.add_argument("--post_id", type=str, default=None, help="Specific post id to backfill")
    parser.add_argument("--dry-run", action="store_true", help="Do not write, only count")
    args = parser.parse_args()
    res = backfill(args.limit, args.since, args.post_id, args.dry_run)
    print(res)
