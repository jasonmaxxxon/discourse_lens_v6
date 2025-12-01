import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("缺少 SUPABASE_URL 或 SUPABASE_KEY，請檢查 .env 設定")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_thread(data: dict, ingest_source: Optional[str] = None):
    """
    將解析好的 Threads 貼文存入 Supabase 的 threads_posts 表
    """
    comments = data.get("comments", [])
    payload = {
        "url": data["url"],
        "author": data["author"],
        "post_text": data["post_text"],
        "post_text_raw": data.get("post_text_raw", ""),
        "like_count": data["metrics"].get("likes", 0),
        "view_count": data["metrics"].get("views", 0),
        "reply_count": len(comments),
        "reply_count_ui": data["metrics"].get("reply_count", 0),
        "repost_count": data["metrics"].get("repost_count", 0),
        "share_count": data["metrics"].get("share_count", 0),
        "images": data.get("images", []),
        "raw_comments": comments,
        "ingest_source": ingest_source,
    }

    try:
        resp = supabase.table("threads_posts").insert(payload).execute()
    except Exception as e:
        payload.pop("ingest_source", None)
        payload.pop("reply_count_ui", None)
        resp = supabase.table("threads_posts").insert(payload).execute()
        print(f"⚠️ ingest_source 欄位缺失，已跳過寫入：{e}")
    print("💾 Saved to DB, id =", resp.data[0]["id"])
