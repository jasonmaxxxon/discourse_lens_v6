### 0. Contract Principles
- Purpose: single source of truth for current DiscourseLens_V5 data model across crawler, quant, LLM overlay, registry enrichment, and API outputs (derived from repo code). Wiring map: see `docs/IO_CIRCUIT_MAP_v1.md`.
- Source of Truth (SoT):
  - Phenomenon identity: DB columns (`threads_posts.phenomenon_id/phenomenon_status/phenomenon_case_id`) written by enrichment/backfill; registry table `narrative_phenomena`.
  - Analysis content: `analysis_json` (AnalysisV4) stored in `threads_posts.analysis_json`.
  - Raw archive: `threads_posts` base columns (post_text, metrics, images, raw_comments, timestamps).
  - API responses: reflect DB-first, fallback to `analysis_json`, default pending.
- Ownership:
  - Crawler/Pipeline writes raw post fields and metrics to `threads_posts`.
  - Analyst/enrichment writes `analysis_json`, `analysis_is_valid`, `analysis_version`, `full_report`, `phenomenon_*` columns.
  - Registry rows (`narrative_phenomena`) populated externally; enrichment reads/writes `phenomenon_id` into posts.
  - Frontend is read-only.

### 1. Entities and Tables (DB Contract)
- threads_posts (Supabase/Postgres)
  - Columns (type best-effort; writers/readers):
    - id (uuid/text): writer crawler/pipelines; reader APIs `/api/posts`, `/api/analysis-json`, library shelf.
    - url (text): writer crawler; reader debug.
    - author (text): writer crawler; reader `/api/posts`.
    - post_text (text): writer crawler; reader `/api/posts`, shelf snippets.
    - post_text_raw (text): writer crawler; reader (none observed).
    - like_count/reply_count/view_count (int): writer crawler; reader `/api/posts`, shelf stats.
    - images (jsonb): writer crawler; reader status page, analyst.
    - raw_comments (jsonb): writer crawler; reader analyst.
    - ai_tags (jsonb): writer analyst; reader `/api/posts`.
    - analysis_json (jsonb): writer analyst/enricher; reader `/api/posts`, `/api/analysis-json`.
    - analysis_is_valid (bool), analysis_version (text), analysis_build_id (text), analysis_invalid_reason (text), analysis_missing_keys (jsonb): writer analyst; reader APIs.
    - raw_json (jsonb), full_report (text): writer analyst; reader `/api/analysis`.
    - cluster_summary, quant_summary (jsonb): writer analyst/quant; reader status/debug.
    - archive_captured_at, archive_build_id, archive_dom_json, archive_html (timestamps/text/jsonb): writer archive; reader `/api/posts`.
    - phenomenon_id (uuid), phenomenon_status (text), phenomenon_case_id (text): writer enrichment/backfill; reader `/api/posts`, `/api/analysis-json`, library endpoints.
    - enrichment_status (text), enrichment_last_error (text), enrichment_retry_count (int), enrichment_queued_at/enrichment_started_at/enrichment_completed_at (timestamptz): writer phenomenon_enricher; reader ops/debug.
    - created_at, captured_at, updated_at (timestamptz): writer DB defaults/crawler; reader `/api/posts`, shelf stats.
  - SoT priority: DB columns are SoT for phenomenon identity; analysis_json is SoT for analysis content; API falls back to analysis_json if columns missing.
- threads_comments (comment evidence SoT, hybrid identity)
  - PK `id` stays the legacy hash (stable) unless already present; native Threads comment id is stored in `source_comment_id` for dedupe/traceability; post_id always populated; parent_source_comment_id captures reply trees when available.
  - Upserts reuse existing rows when (post_id, source_comment_id) matches; fallback hash id ensures cluster links remain valid.
  - Writers: crawler/parser + database.store.sync_comments_to_table; Readers: comments API, Quant/Analyst, clustering joins.
  - Raw evidence kept in raw_json to allow future extraction of missing native ids.
- threads_comment_clusters (cluster registry SoT)
  - id = `post_id::c<cluster_key>`; centroid_embedding_384 stores SBERT 384-d centroid; centroid_embedding reserved for 1536-d future use.
  - keywords/top_comment_ids/size/summary/label preserved; tactics (text[]) and tactic_summary are written back from Analyst; non-blocking FK on threads_comments.cluster_id (NOT VALID) to allow best-effort updates.
- narrative_phenomena (registry)
  - Columns: id (uuid, PK, no default), canonical_name (text), description (text), embedding (vector(1536) legacy), embedding_v768 vector(768, Google text-embedding-004 SoT), status (text default ‘provisional’), minted_by_case_id (text), occurrence_count (int default 1), created_at (timestamptz).
  - Writers: enrichment writes embedding_v768; legacy embedding retained for backward compatibility.
  - Readers: library endpoints `/api/library/phenomena`, `/api/library/phenomena/{id}`.
  - Drift: canonical_name may be null; embedding may be null. Verification uses `vector_dims(embedding_v768)=768`.
- Drift/Risk: registry table existed only after migration; legacy rows in threads_posts may have analysis_json phenomenon but null columns (backfill endpoint/migration provided).

### 2. Analysis Object Contract (AnalysisV4)
- Top-level keys (from `analysis/schema.py`, `build_analysis_json.py`):
  - post: {post_id, author, text, link, images[], timestamp, metrics{likes,views,replies}}
  - phenomenon: {id?, status?, name?, description?, ai_image?} (identity registry-owned; name/description are interpretive)
  - emotional_pulse: {primary?, cynicism, hope, outrage, notes?}
  - segments: [{label, share, samples[{comment_id,user,text,likes}], linguistic_features[]}]
  - narrative_stack: {l1,l2,l3}
  - danger: {bot_homogeneity_score, notes?}
  - summary: {one_line, narrative_type}
  - battlefield: {factions: segments-compatible}
  - full_report: string (optional)
  - Meta added: analysis_version, analysis_build_id, analysis_is_valid, analysis_invalid_reason, analysis_missing_keys, match_ruleset_version, fingerprint_version, registry_version, phenomenon_status, phenomenon_case_id.
- Phenomenon policy: `phenomenon.id` set only by enrichment/registry; pending status allowed. Names from LLM not authoritative.
- Validation: validate_analysis_json requires post.id/text/timestamp and either phenomenon.id or phenomenon.name (pending bypasses name requirement); missing keys populate analysis_missing_keys.
- Minimal AnalysisV4 skeleton:
```json
{
  "post": {"post_id":"...", "author":"...", "text":"...", "link":null, "images":[], "timestamp":"...", "metrics":{"likes":0,"views":null,"replies":null}},
  "phenomenon": {"id":null, "status":"pending", "name":null, "description": "...", "ai_image": null},
  "emotional_pulse": {"primary": null, "cynicism": 0.0, "hope": 0.0, "outrage": 0.0, "notes": null},
  "segments": [],
  "narrative_stack": {"l1": null, "l2": null, "l3": null},
  "danger": null,
  "summary": {"one_line": null, "narrative_type": null},
  "battlefield": {"factions": []},
  "full_report": null,
  "analysis_version": "v4",
  "analysis_build_id": "uuid",
  "analysis_is_valid": true
}
```

### 3. Phenomenon Identity & Registry Contract
- Fingerprint construction (`analysis/phenomenon_fingerprint.py`):
  - Normalize (NFC, strip BOM, collapse whitespace, trim, lowercase, truncate after normalization).
  - TRIGGER: normalized post_text (TRIGGER_MAX_LEN 2400).
  - ARTIFACT: aggregated OCR text from images (full_text/ocr_full_text/text) normalized (ARTIFACT_MAX_LEN 2400).
  - REACTIONS: clusters ordered by size desc then signature hash asc; cluster_signature_hash = sha256 of top-M sample texts (normalized, by like_count desc). Take top1 per cluster + global topK comments by like_count desc, deduped, capped (REACTION_MAX_LEN 3200 per entry).
  - Template produces fingerprint string; case_id = sha256(fingerprint). Constants: FINGERPRINT_VERSION v1, MATCH_RULESET_VERSION v1, REGISTRY_VERSION v1, namespace UUID for deterministic minting.
- Match/Mint (hybrid, `analysis/phenomenon_enricher.py`):
  - Compute embedding from fingerprint text; vector search `narrative_phenomena.embedding` (threshold env `PHENOMENON_MATCH_THRESHOLD`, default 0.86).
  - If best similarity >= threshold → MATCH_EXISTING (use existing phenomenon_id). Else deterministic uuid5 mint.
  - Writes DB columns phenomenon_id/status/case_id and analysis_json phenomenon envelope.
  - Auto-upserts registry row with placeholder canonical_name (`MINTED_<idprefix>`), description placeholder, embedding, minted_by_case_id; occurrence_count increment best-effort.
  - Guard: skip overwrite if analysis_payload already finalized.
- Persistence:
  - threads_posts.phenomenon_id/status/case_id are SoT for identity.
  - Registry table narrative_phenomena holds canonical rows; auto-upsert ensures new ids exist; canonical name/description remain governance-managed.
- Backfill/DEV:
  - SQL `database/migrations/2025-phenomenon-backfill.sql` updates columns from `analysis_json.phenomenon`.
  - DEV endpoint `/api/debug/phenomenon/backfill_from_json` patches missing columns from analysis_json (limit parameter).

### 4. API Contract (Backend → Frontend)
- Common phenomenon envelope behavior: DB-first → analysis_json fallback → default pending; helper `merge_phenomenon_meta`.
- GET /api/posts
  - Params: none.
  - Returns list of posts with fields: id, snippet, created_at, author, like_count, reply_count, view_count, has_analysis, analysis_is_valid, analysis_version, analysis_build_id, archive_captured_at, archive_build_id, has_archive, ai_tags, phenomenon_id, phenomenon_status, phenomenon_case_id, phenomenon_name (canonical if available).
  - Phenomenon source: DB columns preferred; falls back to analysis_json.phenomenon.
  - Errors: JSONResponse 500 with detail and dev_context (phase, trace) on failure.
- GET /api/analysis-json/{post_id}
  - Params: path post_id.
  - Returns: analysis_json (unchanged), analysis_is_valid, analysis_version, analysis_build_id, analysis_invalid_reason, analysis_missing_keys, phenomenon envelope {id,status,case_id,canonical_name,source}.
  - Errors: JSON detail on DB failure; 404 if post/analysis_json missing.
- GET /api/library/phenomena
  - Params: status?, q?, limit? (default 200).
  - Returns list of {id, canonical_name, description, status, total_posts, last_seen_at} aggregated from narrative_phenomena + threads_posts counts.
- GET /api/library/phenomena/{id}
  - Params: limit? (default 20).
  - Returns {meta, stats{total_posts,total_likes,last_seen_at}, recent_posts[{id,created_at,snippet,like_count,phenomenon_status}]}.
- POST /api/library/phenomena/{id}/promote
  - Governance stub: transitions provisional→active; returns {ok,id,status} or 409 if not provisional.
- Debug endpoints:
  - GET /api/debug/latest-post: latest threads_posts snapshot with analysis_json preview.
  - POST /api/debug/phenomenon/backfill_from_json: backfill phenomenon columns from analysis_json; returns counts.
- Other endpoints (unchanged): `/api/run/{pipeline}`, `/api/status/{job}`, `/api/analysis/{post_id}` (full_report), `/proxy_image`, `/run/*` HTML, etc.

### 5. End-to-End Dataflow (Truth Table)
| Stage | Inputs | Transformations | Outputs | Storage | Consumers |
| --- | --- | --- | --- | --- | --- |
| Crawler/Archive | Threads HTML, metrics, comments, images | Parse, clean snippet | Post row fields (post_text, metrics, raw_comments, images) | threads_posts | Pipelines, Analyst |
| Vision/OCR | images | VisionGate → Two-Stage (V1 classify, V2 extract if triggered) | vision_* columns + images enrich | threads_posts.vision_* + images | Analyst (artifact aggregation) |
| Quant/Clustering | comments | embeddings + clustering, homogeneity calc | quant fields on comments (quant_cluster_id, coords), cluster_summary, quant_summary | threads_posts.cluster_summary/quant_summary | Analyst, status |
| Analyst (LLM overlay) | post row + quant outputs + knowledge base | Build AnalysisV4, validate, add summary/layers/tone, optional regex fallback | analysis_json, full_report, analysis meta fields | threads_posts.analysis_json, full_report | API `/api/posts`, `/api/analysis-json` |
| Enrichment (phenomenon) | evidence fingerprint (post_text/OCR/reactions) | Deterministic uuid5 match-or-mint; patch phenomenon id/status/case_id | analysis_json phenomenon fields + DB columns phenomenon_id/status/case_id | threads_posts | API, library |
| API serving | threads_posts rows | Merge DB+JSON identity, format responses | JSON responses | HTTP | Frontend (ArchivePage, NarrativeDetailPage, Library UI) |

### 6. Drift & Risk Register
- Missing registry population: narrative_phenomena rows not auto-created; library endpoints may return empty despite columns being set. Impact: browse shows empty; fix: add registry upsert job.
- Legacy rows with null phenomenon columns but analysis_json present (detected by backfill code). Impact: API pending status; fix: run backfill SQL or DEV endpoint.
- Canonical_name often null (registry not populated). Impact: phenomenon_name fields null; fix: governance populate registry.
- analysis_json and DB id mismatch warning in merge_phenomenon_meta (webapp/main.py); impact: potential drift; fix: reconcile in migration.
- pgvector/registry migration required (database/migrations/2025-phenomenon-registry.sql); if not applied, library endpoints fail. Impact: errors (PGRST205); fix: apply migration.

### 7. Golden Payloads
- Post list item (from docs/integration_snapshot/06_GOLDEN_PAYLOADS.json, before_enrichment):
```json
{
  "id": "post-123",
  "snippet": "post text ...",
  "created_at": "2025-01-01T00:00:00",
  "phenomenon_id": null,
  "phenomenon_status": "pending",
  "phenomenon_case_id": null
}
```
- Analysis JSON response (after enrichment skeleton):
```json
{
  "analysis_json": { "...AnalysisV4 payload..." },
  "analysis_is_valid": true,
  "analysis_version": "v4",
  "analysis_build_id": "11111111-1111-4111-8111-111111111111",
  "analysis_invalid_reason": null,
  "analysis_missing_keys": null,
  "phenomenon": {
    "id": "22222222-2222-4222-8222-222222222222",
    "status": "minted",
    "case_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "canonical_name": null,
    "source": "db_columns"
  }
}
```
- Library index and shelf:
```json
{
  "library_index_item": {
    "id": "22222222-2222-4222-8222-222222222222",
    "canonical_name": "UNKNOWN",
    "description": "new civic meme …",
    "status": "provisional",
    "total_posts": 4,
    "last_seen_at": "2025-01-10T12:00:00Z"
  },
  "library_shelf": {
    "meta": {
      "id": "22222222-2222-4222-8222-222222222222",
      "canonical_name": "UNKNOWN",
      "description": "new civic meme …",
      "status": "provisional"
    },
    "stats": {
      "total_posts": 4,
      "total_likes": 820,
      "last_seen_at": "2025-01-10T12:00:00Z"
    },
    "recent_posts": [
      {
        "id": "post-123",
        "created_at": "2025-01-10T12:00:00Z",
        "snippet": "post text …",
        "like_count": 120,
        "phenomenon_status": "minted"
      }
    ]
  }
}
```
