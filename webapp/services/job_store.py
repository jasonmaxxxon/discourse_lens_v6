import datetime
import logging
import threading
from typing import Any, Dict, Optional

"""
DEPRECATED: Legacy in-memory job store.
Source of Truth for job progress is Supabase job_batches/job_items via webapp.services.job_manager.JobManager.
Kept only for compatibility with legacy routes/templates (/run/* in webapp/app.py and /api/status/{job_id} legacy).
Do not extend; prefer JobManager + /api/jobs/*.
"""

# In-memory job registry guarded by a lightweight lock.
JOBS: dict[str, dict] = {}
_lock = threading.Lock()
_LOG_LIMIT = 200

logger = logging.getLogger(__name__)


def _utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


def create_job(job_id: str, pipeline: str, mode: str, meta: Optional[Dict[str, Any]] = None) -> None:
    meta = meta or {}
    job = {
        "job_id": job_id,
        "pipeline": pipeline,
        "mode": mode,
        "status": "pending",
        "logs": [],
        "post": None,
        "posts": [],
        "summary": "",
        "created_at": _utcnow(),
        "error_stage": None,
        "error_message": None,
    }
    job.update(meta)
    with _lock:
        JOBS[job_id] = job


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        return JOBS.get(job_id)


def set_job_status(job_id: str, status: str, *, stage: Optional[str] = None, message: Optional[str] = None) -> None:
    with _lock:
        job = JOBS.get(job_id)
        if not job:
            return
        job["status"] = status
        if stage is not None:
            job["error_stage"] = stage
        if message is not None:
            job["error_message"] = message
        JOBS[job_id] = job


def append_job_log(job_id: str, line: str) -> None:
    with _lock:
        job = JOBS.get(job_id)
        if not job:
            return
        logs = job.get("logs") or []
        logs.append(line)
        job["logs"] = logs
        JOBS[job_id] = job


def set_job_result(job_id: str, result: Dict[str, Any]) -> None:
    if not isinstance(result, dict):
        return
    with _lock:
        job = JOBS.get(job_id)
        if not job:
            return
        for key, value in result.items():
            job[key] = value
        JOBS[job_id] = job


def cleanup_jobs(max_age_seconds: int = 3600) -> None:
    cutoff = _utcnow() - datetime.timedelta(seconds=max_age_seconds)
    stale_ids: list[str] = []
    with _lock:
        for job_id, job in JOBS.items():
            created_at = job.get("created_at")
            if isinstance(created_at, datetime.datetime) and created_at < cutoff:
                stale_ids.append(job_id)
        for job_id in stale_ids:
            JOBS.pop(job_id, None)


def snapshot_job(job: Dict[str, Any]) -> Dict[str, Any]:
    if not job:
        return {}

    post = job.get("post") or {}
    top_post_id = post.get("id") or post.get("post_id")
    if top_post_id is not None:
        try:
            top_post_id = str(top_post_id)
        except Exception:
            logger.debug("failed to cast post_id to str", exc_info=True)

    posts_list: list[dict[str, Any]] = []
    for p in job.get("posts") or []:
        if not isinstance(p, dict):
            continue
        post_id = p.get("id") or p.get("post_id")
        if post_id is not None:
            try:
                post_id = str(post_id)
            except Exception:
                logger.debug("failed to cast nested post_id to str", exc_info=True)
        posts_list.append(
            {
                "post_id": post_id,
                "has_analysis": bool(p.get("analysis_json")) if isinstance(p.get("analysis_json"), (dict, list, str)) else p.get("has_analysis"),
                "analysis_is_valid": p.get("analysis_is_valid"),
                "analysis_version": p.get("analysis_version"),
                "analysis_build_id": p.get("analysis_build_id"),
                "invalid_reason": p.get("analysis_invalid_reason"),
            }
        )

    logs = job.get("logs") or []
    snapshot = {
        "status": job.get("status"),
        "pipeline": job.get("pipeline"),
        "job_id": job.get("job_id"),
        "mode": job.get("mode"),
        "post_id": top_post_id,
        "posts": posts_list or None,
        "summary": job.get("summary"),
        "logs": logs[-_LOG_LIMIT:] if logs else [],
        "error_stage": job.get("error_stage"),
        "error_message": job.get("error_message"),
    }

    return snapshot


__all__ = [
    "JOBS",
    "create_job",
    "get_job",
    "set_job_status",
    "append_job_log",
    "set_job_result",
    "cleanup_jobs",
    "snapshot_job",
]
