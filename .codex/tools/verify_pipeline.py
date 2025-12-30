#!/usr/bin/env python
import argparse
import os
import sys
import time
from typing import Any, Dict, Optional, Tuple

import requests

POLL_INTERVAL = 3.0
API_BASE = os.environ.get("DL_API_BASE", "http://localhost:8000").rstrip("/")


def _json(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return None


def launch_job(target_url: str) -> str:
    # Primary: /api/run/A (current UI)
    try:
        resp = requests.post(
            f"{API_BASE}/api/run/A",
            json={"url": target_url, "mode": "analyze"},
            timeout=20,
        )
        if resp.ok:
            data = _json(resp) or {}
            job_id = data.get("job_id") or data.get("id")
            if job_id:
                print(f"[launch] via /api/run/A job_id={job_id}")
                return str(job_id)
    except Exception as e:
        print(f"[launch] /api/run/A failed: {e}")

    # Fallback: /api/jobs/
    payload = {
        "pipeline_type": "A",
        "mode": "analyze",
        "input_config": {"url": target_url, "target": target_url, "targets": [target_url]},
    }
    resp = requests.post(f"{API_BASE}/api/jobs/", json=payload, timeout=20)
    if not resp.ok:
        raise RuntimeError(f"POST /api/jobs/ failed ({resp.status_code}) {resp.text}")
    data = _json(resp) or {}
    job_id = data.get("job_id") or data.get("id")
    if not job_id:
        raise RuntimeError(f"No job_id returned from jobs API: {data}")
    print(f"[launch] via /api/jobs job_id={job_id}")
    return str(job_id)


def fetch_job_items(job_id: str) -> Tuple[Optional[Dict[str, Any]], str]:
    url = f"{API_BASE}/api/jobs/{job_id}/items"
    resp = requests.get(url, params={"limit": 1}, timeout=10)
    if not resp.ok:
        return None, f"{resp.status_code}"
    data = _json(resp)
    items = data if isinstance(data, list) else (data or {}).get("items") or (data or {}).get("data")
    if not items:
        return None, "empty"
    return items[0], "ok"


def fetch_job_summary(job_id: str) -> Tuple[Optional[Dict[str, Any]], str]:
    url = f"{API_BASE}/api/jobs/{job_id}/summary"
    resp = requests.get(url, timeout=10)
    if not resp.ok:
        return None, f"{resp.status_code}"
    return _json(resp), "ok"


def fetch_job(job_id: str) -> Tuple[Optional[Dict[str, Any]], str]:
    url = f"{API_BASE}/api/jobs/{job_id}"
    resp = requests.get(url, timeout=10)
    if not resp.ok:
        return None, f"{resp.status_code}"
    return _json(resp), "ok"


def poll_job(job_id: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Returns (final_status, stage, post_id) using only job_items.
    """
    last_stage = None
    last_status = None
    post_id = None

    while True:
        item, label = fetch_job_items(job_id)
        if item is None:
            print(f"[poll] job_id={job_id} no item (err={label}); retrying in {POLL_INTERVAL}s")
            time.sleep(POLL_INTERVAL)
            continue

        stage = str(item.get("stage") or "").lower()
        status = str(item.get("status") or "").lower()
        post_id = item.get("result_post_id") or item.get("post_id") or post_id

        if status in ("", "none", "null"):
            status = "processing"

        if stage != last_stage or status != last_status:
            print(f"[poll] job_id={job_id} stage={stage or '-'} status={status} post_id={post_id or '-'}")
            last_stage = stage
            last_status = status

        if status in ("completed", "done", "success"):
            return "completed", stage, post_id
        if status in ("failed", "error"):
            return "failed", stage, post_id

        time.sleep(POLL_INTERVAL)


def fetch_analysis(post_id: str) -> Dict[str, Any]:
    urls = [
        f"{API_BASE}/api/analysis/{post_id}",
        f"{API_BASE}/api/narrative/{post_id}",
    ]
    for u in urls:
        try:
            resp = requests.get(u, timeout=10)
            if resp.ok:
                data = _json(resp) or {}
                print(f"[analysis] {u} -> {len(resp.text)} bytes")
                return data
        except Exception as e:
            print(f"[analysis] {u} failed: {e}")
    return {}


def analysis_ok(data: Dict[str, Any]) -> bool:
    if not isinstance(data, dict):
        return False
    if data.get("analysis_json"):
        return True
    if isinstance(data.get("full_report"), str) and len(data["full_report"]) > 100:
        return True
    if isinstance(data.get("full_report_markdown"), str) and len(data["full_report_markdown"]) > 100:
        return True
    return False


def main():
    global API_BASE
    parser = argparse.ArgumentParser(description="Verify Pipeline A end-to-end")
    parser.add_argument("url", help="Threads URL to ingest")
    parser.add_argument("--api-base", default=API_BASE, help="API base (default env DL_API_BASE or http://localhost:8000)")
    args = parser.parse_args()

    API_BASE = args.api_base.rstrip("/")

    try:
        job_id = launch_job(args.url)
        status, stage, post_id = poll_job(job_id)
        if status != "completed":
            print(f"[result] job {job_id} failed at stage={stage} post_id={post_id}")
            sys.exit(1)
        if not post_id:
            print(f"[result] job {job_id} completed but no post_id/result_post_id")
            sys.exit(1)

        data = fetch_analysis(str(post_id))
        if analysis_ok(data):
            print(f"[result] PASS job={job_id} post_id={post_id}")
            sys.exit(0)
        print(f"[result] FAIL job={job_id} post_id={post_id} missing analysis content")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"[error] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
