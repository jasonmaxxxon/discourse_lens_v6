import os
import traceback
import asyncio
from typing import Optional, List, Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from webapp.services import pipeline_runner as runner
from webapp.services.job_manager import JobManager

router = APIRouter()

# --- Pydantic models (unchanged) ---


class PipelineBBatchRequest(BaseModel):
    keyword: Optional[str] = None
    urls: Optional[List[str]] = None
    max_posts: int = 20
    exclude_existing: bool = True
    reprocess_policy: str = "skip_if_exists"
    ingest_source: str = "B"
    mode: str = "run"  # "preview" | "run"
    preview: Optional[bool] = None  # legacy field
    pipeline_mode: str = "full"  # "full" | "ingest"
    concurrency: Optional[int] = None
    vision_mode: Optional[str] = None
    vision_stage_cap: Optional[str] = None


class AcademicReference(BaseModel):
    author: str
    year: str
    note: str


class SectionOne(BaseModel):
    executive_summary: str
    phenomenon_spotlight: str
    l1_analysis: str
    l2_analysis: str
    l3_analysis: str
    faction_analysis: str
    strategic_implication: str
    author_influence: str | None = None
    academic_references: list[AcademicReference] | None = None


class AnalysisMeta(BaseModel):
    Post_ID: str
    Timestamp: str
    High_Impact: bool


class QuantifiableTags(BaseModel):
    Sector_ID: str
    Primary_Emotion: str
    Strategy_Code: str
    Civil_Score: int
    Homogeneity_Score: float
    Author_Influence: str


class PostStats(BaseModel):
    Likes: int
    Replies: int
    Views: int


class ClusterInsight(BaseModel):
    name: str
    summary: str
    pct: float | None = None


class DiscoveryChannel(BaseModel):
    Sub_Variant_Name: str
    Is_New_Phenomenon: bool
    Phenomenon_Description: str


class StrategySnippetModel(BaseModel):
    name: str
    intensity: float
    description: str
    example: str
    citation: str


class ToneFingerprintModel(BaseModel):
    assertiveness: float
    cynicism: float
    playfulness: float
    contempt: float
    description: str
    example: str


class FactionSummaryModel(BaseModel):
    name: str
    share: float
    members: List[str]
    sentiment: Optional[float] = None


class CommentSampleModel(BaseModel):
    user: str
    text: str
    likes: int


class NarrativeShiftNodeModel(BaseModel):
    ts: str
    likes: int
    sample_text: str


class SectionTwo(BaseModel):
    narrative_shifts: Optional[List[NarrativeShiftNodeModel]] = None
    competing_frames: Optional[List[str]] = None
    infiltration_signals: Optional[List[str]] = None


class PostAnalysisResponse(BaseModel):
    section_one: SectionOne
    section_two: SectionTwo
    meta: AnalysisMeta
    quantifiable_tags: QuantifiableTags
    post_stats: PostStats
    cluster_insights: List[ClusterInsight]
    discovery_channels: List[DiscoveryChannel]
    strategy_snippets: List[StrategySnippetModel]
    tone_fingerprint: ToneFingerprintModel
    faction_summary: Optional[List[FactionSummaryModel]] = None
    comment_samples: Optional[List[CommentSampleModel]] = None


class RawAnalysisResponse(BaseModel):
    post_id: str
    full_report_markdown: str


class PostListItem(BaseModel):
    id: str
    snippet: str
    created_at: str | None
    author: Optional[str] = None
    like_count: Optional[int] = None
    view_count: Optional[int] = None
    reply_count: Optional[int] = None
    has_analysis: bool = False
    analysis_is_valid: Optional[bool] = None
    analysis_version: Optional[str] = None
    analysis_build_id: Optional[str] = None
    archive_captured_at: Optional[str] = None
    archive_build_id: Optional[str] = None
    has_archive: Optional[bool] = None
    ai_tags: Optional[List[str]] = None
    phenomenon_id: Optional[str] = None
    phenomenon_status: Optional[str] = None
    phenomenon_case_id: Optional[str] = None
    phenomenon_name: Optional[str] = None


class JobPostResult(BaseModel):
    post_id: Optional[str] = None
    has_analysis: Optional[bool] = None
    analysis_is_valid: Optional[bool] = None
    analysis_version: Optional[str] = None
    analysis_build_id: Optional[str] = None
    invalid_reason: Optional[str] = None


class JobResult(BaseModel):
    status: str
    pipeline: str
    job_id: str
    mode: Optional[str] = None
    post_id: Optional[str] = None
    posts: Optional[List[JobPostResult]] = None
    summary: Optional[str] = None
    logs: Optional[List[str]] = None
    error_stage: Optional[str] = None
    error_message: Optional[str] = None


class RunRequest(BaseModel):
    url: str


# --- API endpoints (unchanged logic) ---


@router.post("/run/batch")
async def run_pipeline_b_backend_api(req: PipelineBBatchRequest):
    try:
        mode = req.mode or "run"
        if req.preview is True:
            mode = "preview"
        summary = await runner.process_pipeline_b_backend(
            keyword=req.keyword,
            urls=req.urls,
            max_posts=req.max_posts,
            exclude_existing=req.exclude_existing,
            reprocess_policy=req.reprocess_policy,
            ingest_source=req.ingest_source,
            mode=mode,
            concurrency=getattr(req, "concurrency", None) or 2,
            pipeline_mode=req.pipeline_mode or "full",
            vision_mode=getattr(req, "vision_mode", None) or os.environ.get("VISION_MODE") or "auto",
            vision_stage_cap=getattr(req, "vision_stage_cap", None) or os.environ.get("VISION_STAGE_CAP") or "auto",
        )
        return JSONResponse(summary)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# DEPRECATED: Prefer /api/jobs/ (Supabase JobManager). Legacy wrapper for Pipeline A.
@router.post("/run")
async def api_run_default(req: RunRequest, background_tasks: BackgroundTasks):
    """
    Legacy endpoint: defaults to Pipeline A.
    Now delegates to JobManager (Supabase) to avoid in-memory ghost jobs.
    """
    manager = JobManager()
    pipeline_type = "A"
    mode = "analyze"
    input_config = {"url": req.url, "target": req.url, "targets": [req.url]}

    job_id = await manager.create_job_from_payload(pipeline_type, mode, input_config)
    await manager.start_discovery(job_id)
    loop = asyncio.get_event_loop()
    background_tasks.add_task(loop.create_task, manager.run_worker_mock(job_id))

    return {"job_id": job_id, "status": "pending", "pipeline": pipeline_type}


# DEPRECATED: Prefer /api/jobs/ (Supabase JobManager). Legacy wrapper for Pipeline A/B/C.
@router.post("/run/{pipeline}")
async def api_run_pipeline(pipeline: str, background_tasks: BackgroundTasks, payload: Dict[str, Any]):
    p = (pipeline or "").strip().lower().replace("-", "_")

    alias = {
        "a": "A",
        "pipeline_a": "A",
        "pipelinea": "A",
        "b": "B",
        "pipeline_b": "B",
        "pipelineb": "B",
        "c": "C",
        "pipeline_c": "C",
        "pipelinec": "C",
    }

    pipeline = alias.get(p)
    if pipeline is None:
        raise HTTPException(status_code=400, detail="Unsupported pipeline")

    manager = JobManager()

    if pipeline == "A":
        url = payload.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="Missing url")
        mode = payload.get("mode") or "analyze"
        input_config = {"url": url, "target": url, "targets": [url]}
    elif pipeline == "B":
        keyword = payload.get("keyword")
        urls = payload.get("urls") or []
        lines = payload.get("lines") or []
        targets: list[str] = []
        if keyword:
            targets.append(str(keyword))
        for u in urls:
            if isinstance(u, str):
                targets.append(u)
        for l in lines:
            if isinstance(l, str):
                targets.append(l)
        if not keyword and not targets:
            raise HTTPException(status_code=400, detail="Missing keyword/targets")
        max_posts = int(payload.get("max_posts") or 50)
        mode = payload.get("mode") or "ingest"
        input_config = {"keyword": keyword, "targets": targets, "max_posts": max_posts}
    else:
        max_posts = int(payload.get("max_posts") or 50)
        threshold = int(payload.get("threshold") or 0)
        mode = payload.get("mode") or "ingest"
        input_config = {"max_posts": max_posts, "threshold": threshold}

    job_id = await manager.create_job_from_payload(pipeline, mode, input_config)
    await manager.start_discovery(job_id)
    loop = asyncio.get_event_loop()
    background_tasks.add_task(loop.create_task, manager.run_worker_mock(job_id))

    return {"job_id": job_id, "status": "pending", "pipeline": pipeline}


# DEPRECATED: Prefer /api/jobs/{job_id} (+ /items, /summary). Legacy compatibility endpoint.
@router.get("/status/{job_id}")
async def api_status(job_id: str):
    """
    Legacy compatibility endpoint.
    Delegates to Supabase-backed JobManager; returns a JobResult-shaped payload.
    """
    manager = JobManager()
    header = await manager._table_select_single("job_batches", job_id)
    if not header:
        raise HTTPException(status_code=404, detail="job not found")

    items, _ = await manager.get_job_items(job_id, limit=20)
    summary, _ = await manager.get_job_summary(job_id)

    result = {
        "status": (summary or {}).get("status") or header.get("status"),
        "pipeline": header.get("pipeline_type"),
        "job_id": job_id,
        "mode": header.get("mode"),
        "post_id": None,
        "posts": None,
        "summary": (summary or {}).get("error_summary") or header.get("error_summary") or "",
        "logs": [],
    }

    try:
        return JobResult(**result).model_dump()
    except ValidationError:
        return result


@router.get("/posts", response_model=List[PostListItem])
def list_posts():
    try:
        resp = (
            runner.supabase.table("threads_posts")
            .select("id, post_text, created_at, captured_at, ai_tags, like_count, reply_count, view_count, analysis_json, author, analysis_is_valid, analysis_version, analysis_build_id, archive_captured_at, archive_build_id, phenomenon_id, phenomenon_status, phenomenon_case_id")
            .not_.is_("analysis_json", None)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
    except Exception as e:
        runner.logger.exception("api/posts failed")
        return JSONResponse(
            {
                "detail": f"api/posts failed: {type(e).__name__}: {str(e)}",
                "dev_context": {"phase": "fetch_rows", "trace": traceback.format_exc()},
            },
            status_code=500,
        )

    rows = resp.data or []
    if rows is None:
        rows = []

    items: list[Dict[str, Any]] = []
    for row in rows:
        if row is None:
            continue
        if not isinstance(row, dict):
            try:
                row = dict(row)
            except Exception:
                runner.logger.warning("api/posts skipping non-dict row", extra={"row_type": str(type(row))})
                continue
        try:
            created_at = row.get("created_at") or row.get("captured_at")
            snippet = runner.clean_snippet(row.get("post_text", ""))
            raw_tags = row.get("ai_tags")
            tags_list: list[str] | None = None
            if isinstance(raw_tags, list):
                tags_list = [str(t) for t in raw_tags]
            elif isinstance(raw_tags, dict):
                tags_list = [str(v) for v in raw_tags.values() if v is not None]
            elif raw_tags is not None:
                tags_list = [str(raw_tags)]
            aj_raw = row.get("analysis_json") or {}
            aj = aj_raw if isinstance(aj_raw, dict) else {}
            phen_meta = runner.merge_phenomenon_meta(row, aj)
            items.append(
                {
                    "id": str(row.get("id")),
                    "snippet": snippet,
                    "created_at": created_at,
                    "author": row.get("author"),
                    "like_count": row.get("like_count"),
                    "reply_count": row.get("reply_count"),
                    "view_count": row.get("view_count"),
                    "has_analysis": row.get("analysis_json") is not None,
                    "analysis_is_valid": row.get("analysis_is_valid"),
                    "analysis_version": row.get("analysis_version"),
                    "analysis_build_id": row.get("analysis_build_id"),
                    "archive_captured_at": row.get("archive_captured_at"),
                    "archive_build_id": row.get("archive_build_id"),
                    "has_archive": bool(row.get("archive_captured_at")),
                    "ai_tags": tags_list,
                    "phenomenon_id": phen_meta["id"],
                    "phenomenon_status": phen_meta["status"],
                    "phenomenon_case_id": phen_meta["case_id"],
                    "phenomenon_name": phen_meta.get("canonical_name"),
                }
            )
        except Exception as e:
            dev_context = {
                "phase": "build_item",
                "row_id": row.get("id") if isinstance(row, dict) else None,
                "row_type": str(type(row)),
                "has_analysis_json": isinstance(row.get("analysis_json"), dict),
                "has_phenomenon_json": isinstance((row.get("analysis_json") or {}).get("phenomenon"), dict)
                if isinstance(row.get("analysis_json"), dict)
                else False,
                "trace": traceback.format_exc(),
            }
            runner.logger.exception("api/posts failed in build_item")
            return JSONResponse(
                {
                    "detail": f"api/posts failed: {type(e).__name__}: {str(e)}",
                    "dev_context": dev_context,
                },
                status_code=500,
            )
    return items


@router.get("/analysis-json/{post_id}", response_model=Dict[str, Any])
def get_analysis_json(post_id: str):
    try:
        resp = (
            runner.supabase.table("threads_posts")
            .select(
                "id, analysis_json, analysis_is_valid, analysis_version, analysis_build_id, analysis_invalid_reason, analysis_missing_keys, full_report, updated_at, phenomenon_id, phenomenon_status, phenomenon_case_id"
            )
            .eq("id", post_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        runner.logger.exception("api/analysis-json failed")
        return JSONResponse({"detail": f"api/analysis-json failed: {type(e).__name__}: {str(e)}"}, status_code=500)

    if not resp.data:
        raise HTTPException(status_code=404, detail="Post not found")

    row = resp.data[0]
    analysis_json = row.get("analysis_json")
    if not analysis_json:
        has_full_report = bool(row.get("full_report"))
        raise HTTPException(
            status_code=404,
            detail={
                "reason_code": "analysis_json_missing",
                "has_full_report": has_full_report,
                "hint": "full_report exists but analysis_json missing; check pipeline logs for latest job.",
            },
        )

    phen_meta = runner.merge_phenomenon_meta(row, analysis_json)

    return {
        "analysis_json": analysis_json,
        "analysis_is_valid": row.get("analysis_is_valid"),
        "analysis_version": row.get("analysis_version"),
        "analysis_build_id": row.get("analysis_build_id"),
        "analysis_invalid_reason": row.get("analysis_invalid_reason"),
        "analysis_missing_keys": row.get("analysis_missing_keys"),
        "phenomenon": phen_meta,
    }


@router.get("/library/phenomena")
def list_library_phenomena(status: Optional[str] = None, q: Optional[str] = None, limit: int = 200):
    q_limit = max(1, min(limit or 200, 500))
    try:
        query = runner.supabase.table("narrative_phenomena").select("id, canonical_name, description, status, created_at").limit(q_limit)
        if status:
            query = query.eq("status", status)
        resp = query.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    stats_map = runner.build_phenomenon_post_stats_map()
    results = []
    for row in resp.data or []:
        canon = row.get("canonical_name")
        desc = row.get("description")
        if q:
            needle = q.lower()
            hay = f"{canon or ''} {desc or ''}".lower()
            if needle not in hay:
                continue
        pid = row.get("id")
        pst = stats_map.get(pid, {"total_posts": 0, "total_likes": 0, "last_seen_at": None})
        results.append(
            {
                "id": pid,
                "canonical_name": canon,
                "description": desc,
                "status": row.get("status") or "unknown",
                "total_posts": pst.get("total_posts", 0),
                "last_seen_at": pst.get("last_seen_at"),
            }
        )
    return results


@router.get("/library/phenomena/{phenomenon_id}")
def get_library_phenomenon(phenomenon_id: str, limit: int = 20):
    try:
        meta_resp = (
            runner.supabase.table("narrative_phenomena")
            .select("id, canonical_name, description, status")
            .eq("id", phenomenon_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    if not meta_resp.data:
        raise HTTPException(status_code=404, detail="Phenomenon not found")

    meta = meta_resp.data[0]

    try:
        posts_resp = (
            runner.supabase.table("threads_posts")
            .select("id, created_at, post_text, like_count, phenomenon_status")
            .eq("phenomenon_id", phenomenon_id)
            .order("created_at", desc=True)
            .limit(max(1, min(limit, 100)))
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    posts = posts_resp.data or []
    total_likes = 0
    last_seen_at = None
    for p in posts:
        try:
            total_likes += int(p.get("like_count") or 0)
        except Exception:
            pass
        ts = p.get("created_at")
        if ts and (last_seen_at is None or ts > last_seen_at):
            last_seen_at = ts

    recent_posts = []
    for p in posts:
        recent_posts.append(
            {
                "id": p.get("id"),
                "created_at": p.get("created_at"),
                "snippet": runner.clean_snippet(p.get("post_text") or ""),
                "like_count": p.get("like_count") or 0,
                "phenomenon_status": p.get("phenomenon_status"),
            }
        )

    stats = {
        "total_posts": len(posts),
        "total_likes": total_likes,
        "last_seen_at": last_seen_at,
    }

    return {"meta": meta, "stats": stats, "recent_posts": recent_posts}


@router.post("/library/phenomena/{phenomenon_id}/promote")
def promote_phenomenon(phenomenon_id: str):
    try:
        meta_resp = (
            runner.supabase.table("narrative_phenomena")
            .select("id, status")
            .eq("id", phenomenon_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    if not meta_resp.data:
        raise HTTPException(status_code=404, detail="Phenomenon not found")

    current_status = (meta_resp.data[0] or {}).get("status", "unknown")
    if current_status and str(current_status).lower() != "provisional":
        raise HTTPException(status_code=409, detail=f"Cannot promote from status '{current_status}'")

    try:
        runner.supabase.table("narrative_phenomena").update({"status": "active"}).eq("id", phenomenon_id).execute()
    except Exception as e:
        runner.logger.exception("api/library/phenomena promote failed")
        return JSONResponse({"detail": f"api/library/phenomena promote failed: {type(e).__name__}: {str(e)}"}, status_code=500)

    return {"ok": True, "id": phenomenon_id, "status": "active"}


@router.get("/debug/phenomenon/match/{post_id}")
def debug_phenomenon_match(post_id: str, k: int = 5):
    if not runner.build_evidence_bundle or not runner.embed_text:
        raise HTTPException(status_code=500, detail="Fingerprint/embedding modules unavailable")
    try:
        resp = (
            runner.supabase.table("threads_posts")
            .select("id, post_text, images, raw_comments, cluster_summary")
            .eq("id", post_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")
    if not resp.data:
        raise HTTPException(status_code=404, detail="Post not found")
    row = resp.data[0]
    comments = row.get("raw_comments") or []
    bundle = runner.build_evidence_bundle(
        post_text=row.get("post_text") or "",
        ocr_full_text=None,
        comments=comments if isinstance(comments, list) else [],
        cluster_summary=row.get("cluster_summary") or {},
        images=row.get("images") or [],
    )
    emb = runner.embed_text(bundle.fingerprint)
    try:
        match_resp = (
            runner.supabase.rpc(
                "match_phenomena",
                {
                    "query_embedding": emb,
                    "match_threshold": 0.0,
                    "match_count": max(1, min(k, 20)),
                },
            ).execute()
        )
        candidates = match_resp.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"match_phenomena failed: {e}")

    return {
        "post_id": post_id,
        "fingerprint_hash": runner.embedding_hash(emb) if runner.embedding_hash else None,
        "candidates": candidates,
    }


@router.get("/comments/by-post/{post_id}")
def comments_by_post(post_id: str, limit: int = 50, offset: int = 0, sort: str = "likes"):
    limit = max(1, min(limit, 500))
    try:
        count_resp = (
            runner.supabase.table("threads_comments")
            .select("id")
            .eq("post_id", post_id)
            .execute()
        )
        total = len(count_resp.data or [])
        query = runner.supabase.table("threads_comments").select("id, text, author_handle, like_count, reply_count, created_at").eq("post_id", post_id)
        if sort == "time":
            query = query.order("created_at", desc=True)
        else:
            query = query.order("like_count", desc=True)
        resp = query.range(offset, offset + limit - 1).execute()
    except Exception as e:
        runner.logger.exception("api/comments/by-post failed")
        return JSONResponse({"detail": f"comments by post failed: {type(e).__name__}: {str(e)}"}, status_code=500)

    return {
        "post_id": post_id,
        "total": total,
        "items": resp.data or [],
    }


@router.get("/comments/search")
def comments_search(q: Optional[str] = None, author_handle: Optional[str] = None, post_id: Optional[str] = None, limit: int = 50):
    limit = max(1, min(limit, 200))
    try:
        query = runner.supabase.table("threads_comments").select("id, post_id, text, author_handle, like_count, created_at")
        if q:
            query = query.ilike("text", f"%{q}%")
        if author_handle:
            query = query.eq("author_handle", author_handle)
        if post_id:
            query = query.eq("post_id", post_id)
        resp = query.order("like_count", desc=True).limit(limit).execute()
    except Exception as e:
        runner.logger.exception("api/comments/search failed")
        return JSONResponse({"detail": f"comments search failed: {type(e).__name__}: {str(e)}"}, status_code=500)
    return {"items": resp.data or []}


@router.get("/debug/latest-post")
def get_latest_post_debug():
    try:
        resp = (
            runner.supabase.table("threads_posts")
            .select("*")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    if not resp.data:
        return {"error": "no rows in threads_posts"}

    row = resp.data[0] or {}
    full_report = row.get("full_report") or ""
    preview = full_report[:500] + ("..." if len(full_report) > 500 else "")

    return {
        "id": row.get("id"),
        "url": row.get("url"),
        "created_at": row.get("created_at"),
        "captured_at": row.get("captured_at"),
        "full_report_preview": preview,
        "analysis_json": row.get("analysis_json"),
    }


@router.post("/debug/phenomenon/backfill_from_json")
def backfill_phenomenon_from_json(limit: int = 500):
    try:
        resp = (
            runner.supabase.table("threads_posts")
            .select("id, analysis_json, phenomenon_id, phenomenon_status, phenomenon_case_id")
            .is_("phenomenon_id", None)
            .limit(max(1, min(limit, 1000)))
            .execute()
        )
    except Exception as e:
        runner.logger.exception("backfill fetch failed")
        return JSONResponse({"detail": f"backfill fetch failed: {type(e).__name__}: {str(e)}"}, status_code=500)

    rows = resp.data or []
    updated = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        aj = row.get("analysis_json")
        if not isinstance(aj, dict):
            continue
        phen = aj.get("phenomenon")
        if not isinstance(phen, dict):
            continue
        pid = phen.get("id")
        if not pid:
            continue
        status = phen.get("status") or "pending"
        case_id = aj.get("phenomenon_case_id") or phen.get("case_id")
        try:
            runner.supabase.table("threads_posts").update(
                {
                    "phenomenon_id": pid,
                    "phenomenon_status": status,
                    "phenomenon_case_id": case_id,
                }
            ).eq("id", row.get("id")).execute()
            updated += 1
        except Exception:
            runner.logger.exception("backfill update failed", extra={"post_id": row.get("id")})
            continue

    return {"ok": True, "rows_scanned": len(rows), "rows_updated": updated}


@router.get("/analysis/{post_id}", response_model=RawAnalysisResponse)
def get_analysis(post_id: str):
    try:
        resp = (
            runner.supabase.table("threads_posts")
            .select("id, full_report")
            .eq("id", post_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    if not resp.data:
        raise HTTPException(status_code=404, detail="Post not found")

    row = resp.data[0]
    full_report = row.get("full_report")

    if not full_report:
        raise HTTPException(status_code=404, detail="AI analysis still pending")

    return RawAnalysisResponse(post_id=post_id, full_report_markdown=full_report)


@router.get("/run/batch")
def deprecated_run_batch():
    raise HTTPException(status_code=404, detail="Deprecated")
