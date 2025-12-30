#!/usr/bin/env python3
"""
Fail-fast senior review checks.
Rules:
  A) Backend JSON safety: supabase.table(...).update/insert/upsert payload risk with datetime/uuid.
  B) Frontend hardcoded localhost/8000 base URLs.
  C) Route consistency: /pipeline/progress/:jobId and /narrative/:postId must exist in router.
  D) Polling termination: files with setInterval must also contain clearInterval and terminal-state handling.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

RE_SUPABASE = re.compile(r"supabase\.table\([^)]+\)\.(update|insert|upsert)\(", re.IGNORECASE)
RE_DATETIME_HINT = re.compile(r"datetime\.|date\.|uuid\.|uuid4|datetime\(", re.IGNORECASE)
RE_LOCALHOST = re.compile(r"http://localhost|:8000", re.IGNORECASE)
RE_SET_INTERVAL = re.compile(r"setInterval\s*\(")
RE_CLEAR_INTERVAL = re.compile(r"clearInterval\s*\(")

ROUTER_FILE = Path("dlcs-ui/src/App.tsx")


def git_changed_files() -> List[Path]:
    try:
        res = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True, check=True)
        files = [Path(line.strip()) for line in res.stdout.splitlines() if line.strip()]
        return files
    except Exception:
        return []


def fallback_files() -> List[Path]:
    roots = [Path("webapp"), Path("dlcs-ui")]
    files: List[Path] = []
    for r in roots:
        if r.exists():
            files.extend(r.rglob("*.py"))
            files.extend(r.rglob("*.ts"))
            files.extend(r.rglob("*.tsx"))
            files.extend(r.rglob("*.js"))
            files.extend(r.rglob("*.jsx"))
    return files


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ""


def check_json_safety(files: List[Path]) -> List[str]:
    issues: List[str] = []
    for f in files:
        if f.suffix != ".py":
            continue
        text = read_text_safe(f)
        for i, line in enumerate(text.splitlines(), start=1):
            if RE_SUPABASE.search(line):
                if RE_DATETIME_HINT.search(line) and "isoformat" not in line and "jsonable_encoder" not in line and "_json_safe" not in line:
                    issues.append(f"{f}:{i}: Potential JSON-unsafe supabase payload (datetime/uuid) -> wrap with isoformat/jsonable_encoder")
    return issues


def check_hardcoded_base(files: List[Path]) -> List[str]:
    issues: List[str] = []
    for f in files:
        if "vite.config" in f.name:
            continue
        if f.suffix not in {".ts", ".tsx", ".js", ".jsx", ".py"}:
            continue
        text = read_text_safe(f)
        for i, line in enumerate(text.splitlines(), start=1):
            if RE_LOCALHOST.search(line) and "http://localhost:5173" not in line:
                issues.append(f"{f}:{i}: Hardcoded base URL detected -> use relative /api/... or shared client")
    return issues


def check_routes() -> List[str]:
    issues: List[str] = []
    content = read_text_safe(ROUTER_FILE)
    if "/pipeline/progress/:jobId" not in content:
        issues.append(f"{ROUTER_FILE}: missing /pipeline/progress/:jobId route")
    if "/narrative/:postId" not in content:
        issues.append(f"{ROUTER_FILE}: missing /narrative/:postId route")
    return issues


def check_polling(files: List[Path]) -> List[str]:
    issues: List[str] = []
    for f in files:
        text = read_text_safe(f)
        if "setInterval" in text and f.suffix in {".ts", ".tsx", ".js", ".jsx"}:
            has_set = bool(RE_SET_INTERVAL.search(text))
            has_clear = bool(RE_CLEAR_INTERVAL.search(text))
            has_terminal = "completed" in text or "failed" in text
            if has_set and (not has_clear or not has_terminal):
                issues.append(f"{f}: setInterval present without clearInterval/terminal handling (risk of runaway polling)")
    return issues


def main() -> int:
    files = git_changed_files()
    if not files:
        files = fallback_files()

    issues: List[str] = []
    issues += check_json_safety(files)
    issues += check_hardcoded_base(files)
    issues += check_routes()
    issues += check_polling(files)

    if issues:
        print("senior_review FAILED:")
        for msg in issues:
            print(f"- {msg}")
        return 1

    print("senior_review PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
