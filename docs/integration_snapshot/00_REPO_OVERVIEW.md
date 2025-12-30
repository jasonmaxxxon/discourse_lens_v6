# DiscourseLens V5 — Runtime Overview

## Runtime Components
- **Backend (FastAPI)**: `webapp/main.py` — routers for pipelines, status, analysis retrieval, HTML dashboards; Supabase-backed JobManager (`job_batches`/`job_items`) is the progress SoT (legacy in-memory `JOBS` still present for compatibility).
- **Pipelines**: `pipelines/core.py` invoked by `/api/run/{pipeline}`; long-running work tracked in JobManager; job_items updated per target (stage/status/result_post_id) for UI streaming.
- **Analyst**: `analysis/analyst.py` — stitches crawler data + quant + LLM; writes `threads_posts` with `analysis_json`, `full_report`, `raw_json`, `cluster_summary`, quant metadata.
- **Quant Engine**: `analysis/quant_engine.py` — deterministic clustering/metrics enrichment of comments.
- **Analysis Builder**: `analysis/build_analysis_json.py` + `analysis/schema.py` — builds/validates AnalysisV4 payloads; guards phenomenon id to registry ownership.
- **Phenomenon Enrichment (async)**: `analysis/phenomenon_enricher.py` (ThreadPool, feature-flagged) uses deterministic fingerprint (`analysis/phenomenon_fingerprint.py`).
- **DB Access**: `database/store.py` — Supabase client helpers for saving posts/archives/analysis patches.
- **Frontend**: `dlcs-ui/src/main.tsx` + `dlcs-ui/src/App.tsx` — Vite/React SPA. Key pages: Archive list, Narrative detail, Pipeline triggers, Legacy Home.

## Frontend Entry & Pages
- Entry: `dlcs-ui/src/main.tsx` renders `App`.
- Routing (custom history): `App.tsx` -> `/archive`, `/pipeline/a|b|c`, `/history`, `/demo`, `/narrative/:id`, `/legacy/home`.
- Pipeline A console: `/pipeline/a` single-page launch + inline monitor (no navigation; polls `/api/jobs/{id}` + `/items` + `/summary`).
- Legacy progress wrapper: `/pipeline/progress/:jobId` renders the shared `JobExecutionMonitor`.
- Narrative detail consumes `/api/analysis-json/{postId}` (`NarrativeDetailPage`, `useNarrativeAnalysis`).
- Archive consumes `/api/posts` (`ArchivePage`, `PostSelector`).

## How to Run Locally (from repo docs)
- Backend: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn webapp.main:app --reload --port 8000`
- Frontend: `cd dlcs-ui && npm install && npm run dev -- --port 5173`
- Env: `.env` with `SUPABASE_URL`, `SUPABASE_KEY`, `GEMINI_API_KEY`; Threads cookies in `auth_threads.json`.
