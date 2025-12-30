# senior-review

**When to run (mandatory)**  
- Before commit/PR/merge/release.  
- When a user asks for “review”, “準備 commit”, “merge”, “release”, “fix bug but keep stable”.

**Commands**  
1) `python .codex/tools/senior_review.py`  
2) If frontend was changed and scripts exist, run `npm run lint` / `npm run typecheck` (or report if unavailable).

**Pass criteria**  
- senior_review exits 0 (no JSON-safety risks, no hardcoded localhost, routes consistent, polling has clearInterval).  
- Lint/typecheck succeed or are reported as unavailable.
