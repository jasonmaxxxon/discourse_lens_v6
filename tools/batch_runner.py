"""
CDX-071: Overnight Batch Runner Safety Mode
- Discovers posts (keyword) or reads URLs from a file
- Maintains crash-resume state file with per-URL status/attempts/errors
- Invokes Pipeline A engine (run_pipeline) for each scheduled URL with jitter, retries, and circuit breakers
"""
import argparse
import json
import os
import random
import time
from typing import Dict, List, Any

from pipelines.core import run_pipeline
from event_crawler import discover_thread_urls
from scraper.fetcher import normalize_url


STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"


def load_state(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"urls": {}, "logs": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(path: str, state: Dict[str, Any]) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def classify_rate_limit(err: str) -> bool:
    if not err:
        return False
    low = err.lower()
    return "429" in low or "rate limit" in low or "too many requests" in low


def canonicalize(url: str) -> str:
    try:
        base = url.split("?")[0]
    except Exception:
        base = url
    return normalize_url(base)


def discover_urls(keyword: str, max_posts: int) -> List[str]:
    discovered = discover_thread_urls(keyword, max_posts * 2)
    urls: List[str] = []
    seen = set()
    for p in discovered:
        canon = canonicalize(p.url)
        if canon in seen:
            continue
        seen.add(canon)
        urls.append(canon)
        if len(urls) >= max_posts:
            break
    return urls


def run_batch(keyword: str, max_posts: int, state_file: str, reprocess_policy: str, max_attempts: int, cooldown_every: int):
    state = load_state(state_file)
    urls_state = state.get("urls") or {}
    if not urls_state:
        urls = discover_urls(keyword, max_posts)
        for u in urls:
            urls_state[u] = {"status": STATUS_QUEUED, "attempts": 0, "last_error": None}
        state["urls"] = urls_state
        state["logs"] = state.get("logs") or []
        state["logs"].append(f"Initialized {len(urls)} URLs for keyword={keyword}")
        save_state(state_file, state)

    suspected_rl = 0
    consecutive_failures = 0
    completed = 0
    total = len(urls_state)

    for url, meta in urls_state.items():
        if meta.get("status") == STATUS_SUCCEEDED:
            continue
        if meta.get("status") == STATUS_FAILED and meta.get("attempts", 0) >= max_attempts and reprocess_policy == "skip_if_exists":
            continue

        if suspected_rl >= 3 or consecutive_failures >= 5:
            state["logs"].append(f"Breaker tripped: suspected_rl={suspected_rl}, consecutive_failures={consecutive_failures}")
            break

        meta["status"] = STATUS_RUNNING
        meta["attempts"] = meta.get("attempts", 0) + 1
        save_state(state_file, state)

        try:
            res = run_pipeline(url, ingest_source="B", return_data=True)
            if res:
                meta["status"] = STATUS_SUCCEEDED
                meta["last_error"] = None
                suspected_rl = 0
                consecutive_failures = 0
                completed += 1
            else:
                raise RuntimeError("run_pipeline returned None")
        except Exception as e:
            err_msg = str(e)
            meta["status"] = STATUS_FAILED
            meta["last_error"] = err_msg[:500]
            if classify_rate_limit(err_msg):
                suspected_rl += 1
            else:
                suspected_rl = 0
            consecutive_failures += 1
        save_state(state_file, state)

        # jitter + cooldown
        time.sleep(random.uniform(1.5, 3.5))
        if completed > 0 and completed % cooldown_every == 0:
            time.sleep(random.uniform(15, 30))

    state["logs"].append(
        f"Batch run finished: total={total}, completed={completed}, rl={suspected_rl}, consecutive_failures={consecutive_failures}"
    )
    save_state(state_file, state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Overnight batch runner (safe mode)")
    parser.add_argument("--keyword", required=True, help="Threads search keyword")
    parser.add_argument("--max-posts", type=int, default=50)
    parser.add_argument("--state-file", default="batch_state.json")
    parser.add_argument("--reprocess-policy", choices=["skip_if_exists", "force_all"], default="skip_if_exists")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--cooldown-every", type=int, default=10, help="sleep longer every N successes")
    args = parser.parse_args()
    run_batch(
        keyword=args.keyword,
        max_posts=args.max_posts,
        state_file=args.state_file,
        reprocess_policy=args.reprocess_policy,
        max_attempts=args.max_attempts,
        cooldown_every=args.cooldown_every,
    )
