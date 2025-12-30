import logging
from typing import Any, Dict, Optional

from database.store import supabase

# Optional analyst module; safe import
try:
    from analysis.analyst import generate_commercial_report
except Exception:
    generate_commercial_report = None

logger = logging.getLogger(__name__)


def run_postprocess_for_post(post_id: str) -> Dict[str, Any]:
    """
    Idempotent best-effort postprocess (analyst/quant/enrich) for a single post_id.
    - Fetches threads_posts row
    - If analyst available, runs generate_commercial_report(post, supabase)
    - Writes back returned fields to threads_posts
    """
    if not post_id:
        raise ValueError("post_id is required for postprocess")

    resp = supabase.table("threads_posts").select("*").eq("id", post_id).limit(1).execute()
    row = (resp.data or [None])[0]
    if not row:
        raise RuntimeError(f"post_id {post_id} not found in threads_posts")

    result: Dict[str, Any] = {"post_id": post_id}

    if generate_commercial_report:
        logger.info("[Postprocess] Analyst start post_id=%s", post_id)
        analysis = generate_commercial_report(row, supabase)
        if analysis and not isinstance(analysis, dict):
            raise RuntimeError(f"Analyst returned non-dict: {type(analysis).__name__}")
        if analysis:
            update_fields: Dict[str, Any] = {}
            # Write back common fields if present
            for key in [
                "analysis_json",
                "analysis_is_valid",
                "analysis_invalid_reason",
                "analysis_missing_keys",
                "analysis_version",
                "analysis_build_id",
                "full_report",
                "ai_tags",
                "quant_summary",
                "cluster_summary",
            ]:
                if key in analysis:
                    update_fields[key] = analysis.get(key)
            comments = analysis.get("comments") if isinstance(analysis, dict) else None
            if update_fields:
                supabase.table("threads_posts").update(update_fields).eq("id", post_id).execute()
            if comments and isinstance(comments, list):
                # best-effort writeback of comments if provided
                for c in comments:
                    if isinstance(c, dict):
                        c["post_id"] = post_id
                supabase.table("threads_comments").upsert(comments).execute()
            result["analysis"] = {"updated_fields": list(update_fields.keys())}
            logger.info("[Postprocess] Analyst done post_id=%s fields=%s", post_id, list(update_fields.keys()))
        else:
            logger.warning("[Postprocess] Analyst returned no data post_id=%s", post_id)
    else:
        logger.info("[Postprocess] Analyst module not available; skipping for post_id=%s", post_id)

    return result
