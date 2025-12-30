import os
import uuid
import logging
import random
import asyncio
from datetime import datetime, timezone
from time import perf_counter
from typing import Optional, List, Any, Dict
from starlette.concurrency import run_in_threadpool

from pipelines.core import run_pipeline, run_pipelines
from database.store import supabase, update_post_archive, update_vision_meta
from event_crawler import discover_thread_urls, rank_posts, save_hotlist
from home_crawler import (
    collect_home_posts,
    filter_posts_by_threshold,
    save_home_hotlist,
)
from scraper.fetcher import normalize_url
from analysis.vision_gate import VisionGate
from analysis.vision_worker_two_stage import TwoStageVisionWorker
from webapp.services import job_store
try:
    from fastapi.encoders import jsonable_encoder  # type: ignore
except Exception:
    from datetime import date, datetime

    def jsonable_encoder(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: jsonable_encoder(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [jsonable_encoder(v) for v in obj]
        if isinstance(obj, tuple):
            return [jsonable_encoder(v) for v in obj]
        return obj

# --- AI modules (safe import) ---
try:
    from analysis.analyst import generate_commercial_report
    AI_AVAILABLE = True
    print("✅ AI Modules loaded successfully.")
except ImportError as e:
    print(f"⚠️ AI Module Warning: {e}")
    AI_AVAILABLE = False
    generate_commercial_report = None
try:
    from analysis.phenomenon_fingerprint import build_evidence_bundle
    from analysis.embeddings import embed_text, embedding_hash
except Exception:
    build_evidence_bundle = None
    embed_text = None
    embedding_hash = None

logger = logging.getLogger("dl")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
_JOB_BATCH_EXISTS_CACHE: set[str] = set()


def canonicalize_url(url: str) -> str:
    try:
        base = url.split("?")[0]
    except Exception:
        base = url
    return normalize_url(base)


def fetch_existing_post_ids(urls: List[str]) -> Dict[str, str]:
    if not urls:
        return {}
    existing: Dict[str, str] = {}
    unique_urls = list({u for u in urls if u})
    for i in range(0, len(unique_urls), 200):
        chunk = unique_urls[i : i + 200]
        try:
            resp = supabase.table("threads_posts").select("id,url").in_("url", chunk).execute()
            for row in getattr(resp, "data", None) or []:
                url_val = row.get("url")
                pid = row.get("id")
                if url_val and pid:
                    existing[canonicalize_url(url_val)] = pid
        except Exception as e:
            logger.warning(f"[Pipeline B] fetch existing posts failed: {e}")
    return existing


def build_batch_summary(
    discovery_count: int,
    deduped_count: int,
    selected_count: int,
    skipped_exists: int,
    skipped_policy: int,
    success_count: int,
    fail_count: int,
    logs: List[str],
    failures: List[str],
) -> Dict[str, Any]:
    return {
        "discovery_count": discovery_count,
        "deduped_count": deduped_count,
        "selected_count": selected_count,
        "skipped_exists": skipped_exists,
        "skipped_policy": skipped_policy,
        "success_count": success_count,
        "fail_count": fail_count,
        "failures": failures[:20],
        "logs": logs,
    }


def clean_snippet(text: str, limit: int = 180) -> str:
    if not text:
        return ""
    normalized = " ".join(text.replace("\r", " ").replace("\n", " ").split())
    if len(normalized) > limit:
        return normalized[:limit].rstrip() + "…"
    return normalized


def normalize_like_counts(comments: list) -> list:
    if not comments:
        return comments
    for c in comments:
        if not isinstance(c, dict):
            continue
        val = c.get("like_count")
        if val is None:
            val = c.get("likes", 0)
        try:
            c["like_count"] = int(val)
        except Exception:
            c["like_count"] = 0
    return comments


def merge_phenomenon_meta(row: dict, analysis_json: dict | None) -> dict:
    if not isinstance(row, dict):
        row = {}
    if not isinstance(analysis_json, dict):
        analysis_json = {}
    db_id = row.get("phenomenon_id")
    db_status = row.get("phenomenon_status") or row.get("phenomenon_state")
    db_case = row.get("phenomenon_case_id") or row.get("case_id")

    aj_phen = analysis_json.get("phenomenon") if isinstance(analysis_json, dict) else {}
    if not isinstance(aj_phen, dict):
        aj_phen = {}
    aj_id = aj_phen.get("id")
    aj_status = aj_phen.get("status")
    aj_case = analysis_json.get("phenomenon_case_id") if isinstance(analysis_json, dict) else None
    if aj_case is None:
        aj_case = aj_phen.get("case_id")
    aj_name = aj_phen.get("canonical_name") or aj_phen.get("name")

    source = "default"
    phen_id = None
    phen_status = "pending"
    phen_case = None
    phen_name = None

    if db_id or db_status or db_case:
        phen_id = db_id
        phen_status = db_status or phen_status
        phen_case = db_case
        source = "db_columns"
    elif aj_id or aj_status or aj_case:
        phen_id = aj_id
        phen_status = aj_status or phen_status
        phen_case = aj_case
        phen_name = aj_name
        source = "analysis_json"

    if db_id and aj_id and db_id != aj_id:
        logger.warning(
            "[PhenomenonMeta] DB vs analysis_json id mismatch",
            extra={"db_id": db_id, "aj_id": aj_id, "post_id": row.get("id")},
        )

    return {
        "id": phen_id,
        "status": phen_status or "pending",
        "case_id": phen_case,
        "canonical_name": phen_name,
        "source": source,
    }


def make_job_logger(job_id: str):
    def _logger(message: str) -> None:
        job_store.append_job_log(job_id, message)
        print(f"[{job_id[:8]}] {message}")

    return _logger


def _safe_log_url(url: str) -> str:
    try:
        return (url or "").split("?")[0]
    except Exception:
        return str(url)


def _log_comments_summary(logger_obj: logging.Logger, comments: list | None) -> None:
    if comments and isinstance(comments, list):
        try:
            logger_obj.info("📦 comments_ready count=%s (bulk write candidate)", len(comments))
        except Exception:
            pass


def _update_stage(item_id: str | None, stage: str) -> None:
    """
    Best-effort stage update when no stage_cb is provided or it fails.
    """
    if not item_id or not supabase:
        return
    try:
        supabase.rpc("set_job_item_stage", {"p_item_id": item_id, "p_stage": stage}).execute()
    except Exception as e:
        logger.warning("[Runner] stage update failed item_id=%s stage=%s err=%s", item_id, stage, e)


def _job_batch_exists(job_id: Optional[str]) -> bool:
    if not job_id or not supabase:
        return False
    if job_id in _JOB_BATCH_EXISTS_CACHE:
        return True
    try:
        resp = supabase.table("job_batches").select("id").eq("id", job_id).limit(1).execute()
        exists = bool(resp.data)
        if exists:
            _JOB_BATCH_EXISTS_CACHE.add(job_id)
        return exists
    except Exception as e:
        logger.debug("[Runner] job_batch existence check failed job_id=%s err=%s", job_id, e)
        return False


def _progressive_job_item_update(
    job_id: Optional[str],
    target: str,
    stage: str,
    status: str = "processing",
    result_post_id: Any = None,
    error: Optional[str] = None,
) -> None:
    """
    Best-effort: ensure job_items reflects incremental progress so UI can stream results.
    Only runs when job_id exists in job_batches to avoid polluting unrelated runs.
    """
    if not _job_batch_exists(job_id):
        return
    if not supabase:
        return

    patch: Dict[str, Any] = {
        "stage": stage,
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if result_post_id is not None:
        patch["result_post_id"] = str(result_post_id)
    if error:
        patch["error_log"] = error[:500]

    try:
        res = supabase.table("job_items").update(patch).eq("job_id", job_id).eq("target_id", target).execute()
        if not res.data:
            supabase.table("job_items").insert(
                {
                    "job_id": job_id,
                    "target_id": target,
                    "status": status,
                    "stage": stage,
                    "result_post_id": str(result_post_id) if result_post_id is not None else None,
                    "error_log": error[:500] if error else None,
                }
            ).execute()
    except Exception as e:
        logger.warning("[ops] job_item stage set failed (non-fatal): %s", e)


def build_phenomenon_post_stats_map() -> dict[str, dict[str, Any]]:
    try:
        resp = (
            supabase.table("threads_posts")
            .select("phenomenon_id, created_at, like_count")
            .not_.is_("phenomenon_id", None)
            .execute()
        )
    except Exception as e:
        logger.warning("Failed to fetch phenomenon post stats", extra={"error": str(e)})
        return {}

    stats: dict[str, dict[str, Any]] = {}
    for row in resp.data or []:
        pid = row.get("phenomenon_id")
        if not pid:
            continue
        entry = stats.setdefault(pid, {"total_posts": 0, "total_likes": 0, "last_seen_at": None})
        entry["total_posts"] += 1
        try:
            entry["total_likes"] += int(row.get("like_count") or 0)
        except Exception:
            pass
        ts = row.get("created_at")
        if ts and (entry["last_seen_at"] is None or ts > entry["last_seen_at"]):
            entry["last_seen_at"] = ts
    return stats


def should_reprocess(reprocess_policy: str, keyword_hit: bool) -> bool:
    if reprocess_policy == "force_all":
        return True
    if reprocess_policy == "force_if_keyword_hit" and keyword_hit:
        return True
    return False


def run_pipeline_a_job(job_id: str, url: str, item_id: str | None = None, stage_cb=None) -> str:
    """
    Blocking runner orchestrator for Pipeline A (Fetch -> Vision -> Analyst -> Store).
    - Uses stage_cb(stage) if provided to report stage transitions (fetch, vision, analyst, store).
    - Returns deterministic post_id (string) from run_pipeline result.
    - Does not swallow exceptions; re-raises after logging.
    """
    safe_url = _safe_log_url(url)
    logger.info("[Runner] ENTER job_id=%s item_id=%s url=%s", job_id, item_id, safe_url)

    def _stage(stage: str):
        if stage_cb:
            try:
                stage_cb(stage)
                return
            except Exception:
                logger.warning("[Runner] stage_cb failed stage=%s item_id=%s", stage, item_id, exc_info=True)
        _update_stage(item_id, stage)

    def _logger(message: str) -> None:
        logger.info("[RunnerLog][%s] %s", job_id, message)

    t0 = perf_counter()

    # Fetch
    _stage("fetch")
    start = perf_counter()
    try:
        logger.info("[Runner] DISPATCH start job_id=%s url=%s", job_id, safe_url)
        result = run_pipeline(url, ingest_source="A", return_data=True, logger=_logger)
        duration = perf_counter() - start
        logger.info("[Runner] DISPATCH end job_id=%s url=%s dur=%.2fs", job_id, safe_url, duration)
    except Exception:
        duration = perf_counter() - start
        logger.exception("[Runner] EXCEPTION job_id=%s url=%s dur=%.2fs", job_id, safe_url, duration)
        raise

    if not isinstance(result, dict):
        logger.warning("[Runner] run_pipeline returned non-dict or None job_id=%s url=%s", job_id, safe_url)
        raise RuntimeError("run_pipeline returned invalid result")

    try:
        summary = f"keys={list(result.keys())}"
    except Exception:
        summary = "<uninspectable>"
    logger.info("[Runner] Result summary job_id=%s url=%s %s", job_id, safe_url, summary)
    _log_comments_summary(logger, result.get("comments") or result.get("raw_comments"))

    post_id = result.get("id") or result.get("post_id")
    if not post_id:
        raise RuntimeError("INGEST_NO_POST_ID")
    post_id = str(post_id)

    # Vision stage (best-effort; raise on failure if images exist)
    _stage("vision")
    images = result.get("images") or []
    if images:
        try:
            vision_mode = (os.environ.get("VISION_MODE") or "auto").lower()
            vision_stage_cap = (os.environ.get("VISION_STAGE_CAP") or "auto").lower()
            gate = VisionGate()
            comments = result.get("comments") or result.get("raw_comments") or []
            decision = gate.evaluate(
                post_id=post_id,
                images_count=len(images),
                post_text=(result.get("post_text") or result.get("post_text_raw") or ""),
                comments=comments if isinstance(comments, list) else [],
                vision_mode=vision_mode,
                metrics={
                    "view_count": result.get("view_count") or (result.get("metrics") or {}).get("views"),
                    "like_count": result.get("like_count") or (result.get("metrics") or {}).get("likes"),
                    "reply_count": result.get("reply_count") or (result.get("metrics") or {}).get("reply_count"),
                    "metrics_reliable": True,
                },
            )
            stage_ran = "none"
            v1 = {}
            v2 = {}
            updated_images = images

            if images:
                first = images[0] if images else {}
                src = None
                if isinstance(first, dict):
                    src = first.get("cdn_url") or first.get("original_src") or first.get("src")
                if src and str(src).startswith("http"):
                    worker = TwoStageVisionWorker(gemini_api_key=os.environ.get("GEMINI_API_KEY") or "")
                    v1 = worker.run_v1(src)
                    stage_ran = "v1"
                    should_v2 = False
                    if vision_stage_cap in ("v2", "auto"):
                        if v1.get("has_text") or v1.get("is_screenshot") or (v1.get("text_density") or "").lower() in ("medium", "high"):
                            should_v2 = True
                    if vision_stage_cap == "v1":
                        should_v2 = False
                    if should_v2:
                        v2 = worker.run_v2(src)
                        stage_ran = "v2"

                    enriched_first = dict(first) if isinstance(first, dict) else {}
                    enriched_first["scene_label"] = v2.get("scene_label") or v1.get("category") or enriched_first.get("scene_label")
                    if stage_ran == "v2":
                        enriched_first["full_text"] = v2.get("extracted_text") or ""
                        enriched_first["context_desc"] = v2.get("context_desc") or ""
                        enriched_first["visual_rhetoric"] = v2.get("visual_rhetoric") or ""
                    else:
                        enriched_first["context_desc"] = v1.get("notes") or ""
                    updated_images = [enriched_first] + (images[1:] if len(images) > 1 else [])
                    result["images"] = updated_images

            fields = decision.to_db_fields(vision_mode=vision_mode, stage_ran=stage_ran)
            fields["vision_v1"] = v1 or None
            fields["vision_v2"] = v2 or None
            update_vision_meta(SUPABASE_URL, SUPABASE_KEY, post_id, vision_fields=fields, images=updated_images)
            logger.info("[Runner] Vision stage completed post_id=%s stage=%s", post_id, stage_ran)
        except Exception:
            logger.exception("[Runner] Vision stage failed (soft-fail) post_id=%s", post_id)
    else:
        logger.info("[Runner] Vision skipped (no images) post_id=%s", post_id)

    # Analyst / Enrich
    _stage("analyst")
    if not generate_commercial_report:
        raise RuntimeError("Analyst module not available")
    try:
        analysis = generate_commercial_report(result, supabase)
        if analysis and not isinstance(analysis, dict):
            raise RuntimeError(f"Analyst returned non-dict: {type(analysis).__name__}")
        if analysis:
            update_fields: Dict[str, Any] = {}
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
            if update_fields:
                update_fields = jsonable_encoder(update_fields)
                supabase.table("threads_posts").update(update_fields).eq("id", post_id).execute()
            logger.info("[Runner] Analyst stage completed post_id=%s fields=%s", post_id, list(update_fields.keys()))
        else:
            raise RuntimeError("Analyst returned no data")
    except Exception:
        logger.exception("[Runner] Analyst stage failed post_id=%s", post_id)
        raise

    _stage("store")
    logger.info("[Runner] STORE stage post_id=%s vision_ran=%s analyst_ran=True dur=%.2fs", post_id, bool(images), perf_counter() - t0)
    return post_id


def run_pipeline_b_job(job_id: str, keyword: str, max_posts: int, mode: str, reprocess_policy: str = "skip_if_exists"):
    log = make_job_logger(job_id)
    job = job_store.get_job(job_id)
    if not job:
        return

    try:
        job_store.set_job_status(job_id, "running")
        log(f"🧵 Pipeline B 任務開始，keyword = {keyword}")

        discovered = discover_thread_urls(keyword, max_posts * 2)
        discovery_count = len(discovered)
        ranked = rank_posts(discovered)
        selected = ranked[:max_posts]
        log(f"📥 本次發現 {discovery_count} 篇，選取 {len(selected)} 篇貼文")

        if mode == "hotlist":
            filepath = save_hotlist(selected, keyword)
            job_store.set_job_result(
                job_id,
                {
                    "posts": [],
                    "summary": f"Pipeline B 完成，已輸出 hotlist（{len(selected)} 篇，關鍵字：{keyword}）",
                },
            )
            job_store.set_job_status(job_id, "done")
            log(f"✅ Pipeline B 完成，hotlist 已輸出：{filepath}")
            return

        urls = []
        canonical_to_raw: Dict[str, str] = {}
        for p in selected:
            canon = canonicalize_url(p.url)
            if canon in canonical_to_raw:
                continue
            canonical_to_raw[canon] = p.url
            urls.append(canon)

        existing_map = fetch_existing_post_ids(urls)
        scheduled: List[str] = []
        skipped: List[str] = []

        for canon in urls:
            exists = canon in existing_map
            if not exists:
                scheduled.append(canon)
            else:
                if should_reprocess(reprocess_policy, keyword_hit=True):
                    scheduled.append(canon)
                else:
                    skipped.append(canon)

        log(
            f"🧮 Discovery={discovery_count}, deduped={len(urls)}, scheduled={len(scheduled)}, skipped={len(skipped)} policy={reprocess_policy}"
        )

        posts: List[dict] = []
        success = 0
        failures: List[str] = []
        for idx, url in enumerate(scheduled, start=1):
            try:
                _progressive_job_item_update(job_id, url, "running", status="processing")
                log(f"[{idx}/{len(scheduled)}] 🔗 Processing {url}")
                data = run_pipeline(url, ingest_source="B", return_data=True, logger=log)
                if data:
                    post_id = data.get("id") or data.get("post_id")
                    data["snippet"] = clean_snippet(data.get("post_text", ""))
                    data["images"] = data.get("images") or []
                    posts.append(data)
                    success += 1
                    if post_id:
                        _progressive_job_item_update(job_id, url, "completed_post", status="processing", result_post_id=post_id)
                else:
                    failures.append(url)
            except Exception as e:
                failures.append(f"{url} ({e})")
                _progressive_job_item_update(job_id, url, "failed_post", status="processing", error=str(e))

        summary = (
            f"Pipeline B 完成，已處理 {success}/{len(scheduled)} 篇（關鍵字：{keyword}, 跳過 {len(skipped)}）"
        )
        job_store.set_job_result(
            job_id,
            {
                "posts": posts or [],
                "summary": summary or "",
            },
        )
        job_store.set_job_status(job_id, "done")
        log(f"✅ Pipeline B 完成，success={success}, failed={len(failures)}, skipped={len(skipped)}")
        if failures:
            log(f"❗ 失敗列表: {failures[:5]}")
    except Exception as e:
        job_store.set_job_status(job_id, "error")
        log(f"❌ Pipeline B 任務失敗：{e}")


async def process_pipeline_b_backend(
    keyword: Optional[str],
    urls: Optional[List[str]],
    max_posts: int,
    exclude_existing: bool,
    reprocess_policy: str,
    ingest_source: str = "B",
    mode: str = "run",
    concurrency: int = 2,
    pipeline_mode: str = "full",
    vision_mode: str = "auto",
    vision_stage_cap: str = "auto",
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    vision_mode = (vision_mode or os.environ.get("VISION_MODE") or "auto").lower()
    vision_stage_cap = (vision_stage_cap or os.environ.get("VISION_STAGE_CAP") or "auto").lower()
    logs: List[str] = []
    max_posts = max(1, min(max_posts or 20, 20))
    concurrency = max(1, min(concurrency or 2, 3))

    candidates: List[str] = []
    if keyword:
        discovered = await run_in_threadpool(discover_thread_urls, keyword, max_posts * 2)
        logs.append(f"discovered_via_keyword={len(discovered)}")
        for p in discovered:
            canon = canonicalize_url(p.url)
            candidates.append(canon)

    for url in urls or []:
        candidates.append(canonicalize_url(url))

    deduped = list({u for u in candidates if u})
    discovery_count = len(candidates)
    deduped_count = len(deduped)
    if deduped_count > max_posts:
        deduped = deduped[:max_posts]

    existing_map = fetch_existing_post_ids(deduped)
    scheduled: List[str] = []
    skipped_exists: List[str] = []
    skipped_policy: List[str] = []
    items: List[Dict[str, Any]] = []
    for canon in deduped:
        exists = canon in existing_map
        keyword_hit = True if keyword else False
        if exists and exclude_existing and not should_reprocess(reprocess_policy, keyword_hit):
            skipped_exists.append(canon)
            items.append(
                {
                    "canonical_url": canon,
                    "decision": "skipped_exists",
                    "reason": "exists",
                    "existing_post_id": existing_map.get(canon),
                }
            )
            continue
        if exists and not should_reprocess(reprocess_policy, keyword_hit):
            skipped_policy.append(canon)
            items.append(
                {
                    "canonical_url": canon,
                    "decision": "skipped_policy",
                    "reason": "policy_skip",
                    "existing_post_id": existing_map.get(canon),
                }
            )
            continue
        scheduled.append(canon)
        items.append(
            {
                "canonical_url": canon,
                "decision": "selected",
                "reason": None,
                "existing_post_id": existing_map.get(canon),
            }
        )

    logs.append(
        f"deduped={deduped_count}, selected={len(scheduled)}, skipped_exists={len(skipped_exists)}, skipped_policy={len(skipped_policy)}, policy={reprocess_policy}, exclude_existing={exclude_existing}"
    )

    if mode == "preview":
        summary = build_batch_summary(
            discovery_count=discovery_count,
            deduped_count=deduped_count,
            selected_count=len(scheduled),
            skipped_exists=len(skipped_exists),
            skipped_policy=len(skipped_policy),
            success_count=0,
            fail_count=0,
            logs=logs,
            failures=[],
        )
        summary["items"] = items[:max_posts]
        summary["posts"] = []
        return summary

    success = 0
    fail = 0
    failures: List[str] = []
    posts: List[dict] = []

    async def run_one(idx: int, url: str, sem: asyncio.Semaphore):
        nonlocal success, fail
        async with sem:
            try:
                logs.append(f"[{idx}/{len(scheduled)}] BEGIN {url}")
                _progressive_job_item_update(job_id, url, "running", status="processing")
                ingest_res = await run_in_threadpool(
                    run_pipeline,
                    url,
                    ingest_source,
                    True,
                    logs.append,
                )
                await asyncio.sleep(random.uniform(0.5, 1.0))
                if not ingest_res:
                    raise RuntimeError("run_pipeline returned None")
                post_id = ingest_res.get("id")
                item_base = {
                    "canonical_url": url,
                    "post_id": post_id,
                }

                if pipeline_mode == "ingest":
                    posts.append(ingest_res)
                    success += 1
                    items.append({**item_base, "status": "succeeded", "reason": None, "stage": "ingest"})
                    logs.append(f"[{idx}/{len(scheduled)}] OK ingest {url} post_id={post_id}")
                    if post_id:
                        _progressive_job_item_update(job_id, url, "completed_post", status="processing", result_post_id=post_id)
                    return

                vm = (vision_mode or "auto").lower()
                vcap = (vision_stage_cap or "auto").lower()
                try:
                    if ingest_res.get("images"):
                        post_id_str = str(ingest_res.get("id"))
                        gate = VisionGate()
                        dec = gate.evaluate(
                            post_id=post_id_str,
                            images_count=len(ingest_res.get("images") or []),
                            post_text=(ingest_res.get("post_text") or ingest_res.get("post_text_raw") or ""),
                            comments=(ingest_res.get("comments") or ingest_res.get("raw_comments") or []),
                            vision_mode=vm,
                            metrics={
                                "view_count": ingest_res.get("view_count"),
                                "like_count": ingest_res.get("like_count"),
                                "reply_count": ingest_res.get("reply_count"),
                                "metrics_reliable": True,
                            },
                        )
                        update_vision_meta(SUPABASE_URL, SUPABASE_KEY, post_id_str, vision_fields=dec.to_db_fields(vm, "none"))

                        if dec.run_v1:
                            worker = TwoStageVisionWorker(gemini_api_key=os.environ.get("GEMINI_API_KEY") or "")
                            imgs = ingest_res.get("images") or []
                            first = imgs[0] if imgs else {}
                            src = (first or {}).get("cdn_url") or (first or {}).get("original_src") or (first or {}).get("src")
                            stage_ran = "none"
                            v1 = {}
                            v2 = {}
                            updated_images = imgs

                            if src and str(src).startswith("http"):
                                v1 = worker.run_v1(src)
                                stage_ran = "v1"
                                should_v2 = False
                                if vcap in ("v2", "auto"):
                                    if v1.get("has_text") or v1.get("is_screenshot") or (v1.get("text_density") or "").lower() in ("medium", "high"):
                                        should_v2 = True
                                if vcap == "v1":
                                    should_v2 = False
                                if should_v2:
                                    v2 = worker.run_v2(src)
                                    stage_ran = "v2"

                                enriched_first = dict(first)
                                enriched_first["scene_label"] = v2.get("scene_label") or v1.get("category") or enriched_first.get("scene_label")
                                if stage_ran == "v2":
                                    enriched_first["full_text"] = v2.get("extracted_text") or ""
                                    enriched_first["context_desc"] = v2.get("context_desc") or ""
                                    enriched_first["visual_rhetoric"] = v2.get("visual_rhetoric") or ""
                                else:
                                    enriched_first["context_desc"] = v1.get("notes") or ""

                                updated_images = [enriched_first] + (imgs[1:] if len(imgs) > 1 else [])

                            fields = dec.to_db_fields(vm, stage_ran)
                            fields["vision_v1"] = v1 or None
                            fields["vision_v2"] = v2 or None
                            update_vision_meta(SUPABASE_URL, SUPABASE_KEY, post_id_str, vision_fields=fields, images=updated_images)

                            ingest_res["images"] = updated_images
                            logs.append(f"[{idx}/{len(scheduled)}] stage=vision {stage_ran} post_id={post_id_str}")
                except Exception as ve:
                    logs.append(f"[{idx}/{len(scheduled)}] stage=vision FAIL: {ve}")

                logs.append(f"[{idx}/{len(scheduled)}] stage=analyst start url={url}")
                analyst_res = await run_in_threadpool(
                    generate_commercial_report,
                    ingest_res,
                    supabase,
                )
                logs.append(f"[{idx}/{len(scheduled)}] stage=analyst end url={url}")
                posts.append(analyst_res or ingest_res)
                success += 1
                items.append(
                    {
                        **item_base,
                        "status": "succeeded",
                        "reason": None,
                        "stage": "full",
                        "phenomenon_id": (analyst_res or {}).get("phenomenon_id") or ingest_res.get("phenomenon_id"),
                    }
                )
                logs.append(f"[{idx}/{len(scheduled)}] OK full {url} post_id={post_id}")
                if post_id:
                    _progressive_job_item_update(job_id, url, "completed_post", status="processing", result_post_id=post_id)
            except Exception as e:
                fail += 1
                failures.append(f"{url} ({e})")
                items.append(
                    {
                        "canonical_url": url,
                        "decision": "selected",
                        "status": "failed",
                        "stage": "ingest" if "run_pipeline" in str(e) else "full",
                        "reason": str(e),
                    }
                )
                logs.append(f"[{idx}/{len(scheduled)}] FAIL {url}: {e}")
                _progressive_job_item_update(job_id, url, "failed_post", status="processing", error=str(e))

    async def run_all():
        sem = asyncio.Semaphore(concurrency)
        tasks = []
        for idx, url in enumerate(scheduled, start=1):
            await asyncio.sleep(random.uniform(0.2, 0.6))
            tasks.append(asyncio.create_task(run_one(idx, url, sem)))
        if tasks:
            await asyncio.gather(*tasks)

    if scheduled:
        await run_all()

    summary = build_batch_summary(
        discovery_count=discovery_count,
        deduped_count=deduped_count,
        selected_count=len(scheduled),
        skipped_exists=len(skipped_exists),
        skipped_policy=len(skipped_policy),
        success_count=success,
        fail_count=fail,
        logs=logs,
        failures=failures,
    )
    summary["posts"] = posts
    summary["items"] = items
    return summary


def run_pipeline_c_job(job_id: str, max_posts: int, threshold: int, mode: str):
    log = make_job_logger(job_id)
    job = job_store.get_job(job_id)
    if not job:
        return

    try:
        job_store.set_job_status(job_id, "running")
        log(f"🧵 Pipeline C 任務開始，max_posts = {max_posts}, threshold = {threshold}")

        posts = collect_home_posts(max_posts)
        filtered = filter_posts_by_threshold(posts, threshold)
        log(f"📥 Home 抽樣 {len(posts)} 篇，門檻後剩 {len(filtered)} 篇")

        if mode == "hotlist":
            filepath = save_home_hotlist(filtered)
            job_store.set_job_result(
                job_id,
                {
                    "posts": [],
                    "summary": f"Pipeline C 完成，已輸出 hotlist（{len(filtered)} 篇樣本，threshold={threshold}）",
                },
            )
            job_store.set_job_status(job_id, "done")
            log(f"✅ Pipeline C 完成，hotlist 已輸出：{filepath}")
            return

        urls = [p.url for p in filtered]
        posts = run_pipelines(urls, ingest_source="C", logger=log)
        summary = f"Pipeline C 完成，已抓取 {len(posts)} 篇個人主頁樣本（threshold={threshold}）"

        normalized_posts: list[dict] = []
        for p in posts:
            p["images"] = p.get("images") or []
            normalized_posts.append(p)
        job_store.set_job_result(
            job_id,
            {
                "posts": normalized_posts,
                "summary": summary or "",
            },
        )
        job_store.set_job_status(job_id, "done")
        log(f"✅ Pipeline C 完成，共 {len(normalized_posts)} 篇。")
    except Exception as e:
        job_store.set_job_status(job_id, "error")
        log(f"❌ Pipeline C 任務失敗：{e}")


__all__ = [
    "canonicalize_url",
    "fetch_existing_post_ids",
    "build_batch_summary",
    "clean_snippet",
    "normalize_like_counts",
    "merge_phenomenon_meta",
    "build_phenomenon_post_stats_map",
    "should_reprocess",
    "run_pipeline_a_job",
    "run_pipeline_b_job",
    "process_pipeline_b_backend",
    "run_pipeline_c_job",
]
