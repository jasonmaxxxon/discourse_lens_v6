### 0. Contract Principles
- Assignment SoT (post → phenomenon link): `threads_posts.phenomenon_id`, `phenomenon_status`, `phenomenon_case_id` (set by enrichment/backfill).
- Definition SoT (phenomenon entity): `public.narrative_phenomena` rows (id, status, canonical_name/description if curated). Do not rely on `analysis_json.phenomenon` for identity logic.
- Raw archive SoT: `threads_posts` crawler fields (post_text/images/raw_comments/metrics/timestamps). Legacy cache: `raw_comments`; comments SoT = `threads_comments`.
- Interpretive snapshot: `threads_posts.analysis_json` (AnalysisV4) is descriptive only; not authoritative for identity or registry.
- Fingerprint/identity changes must bump `FINGERPRINT_VERSION` and include a migration/backfill plan for affected columns.

### 1. Entities and Tables (DB Contract)
- threads_posts (operational store)
  - Identity columns: phenomenon_id (uuid), phenomenon_status (text), phenomenon_case_id (text) — written by enrichment/backfill; read by APIs and library.
  - Analysis columns: analysis_json (AnalysisV4), analysis_is_valid, analysis_version, analysis_build_id, analysis_invalid_reason, analysis_missing_keys, full_report, raw_json.
  - Vision columns (CDX-081): vision_mode, vision_need_score, vision_reasons, vision_stage_ran (none/v1/v2), vision_v1, vision_v2, vision_sim_post_comments, vision_metrics_reliable, vision_updated_at.
  - Raw/archive: post_text, images (jsonb), raw_comments (jsonb legacy), like_count/reply_count/view_count, author, url, created_at/captured_at/updated_at.
  - Quant/meta: cluster_summary, quant_summary, ai_tags.
  - Archive: archive_captured_at, archive_build_id, archive_dom_json, archive_html.
  - SoT: DB columns outrank analysis_json for phenomenon identity; analysis_json is SoT for interpretive fields.
- narrative_phenomena (registry)
  - Columns: id (uuid PK), canonical_name (nullable), description (nullable), embedding vector(1536) nullable, status text default 'provisional', minted_by_case_id text, occurrence_count int default 1, created_at timestamptz default now().
  - SoT: registry is the definition authority; upserts must not overwrite curated canonical_name/description without governance.
- threads_comments (raw evidence SoT for comments)
  - Columns: id (text PK), post_id (bigint FK -> threads_posts), text, author_handle, like_count, reply_count, created_at, raw_json, cluster_label/tactic_tag (null), embedding vector(1536) (nullable), inserted_at/updated_at.
  - Writers: dual write in `database/store.py` on ingest; backfill script `database/backfill_comments_from_posts.py`.
  - Readers: comment APIs, future search/analytics. SoT for comment evidence; raw_comments retained as legacy snapshot.

### 2. Analysis Object Contract (AnalysisV4)
- Top-level: post{post_id,author,text,link?,images[],timestamp,metrics{likes,views,replies}}, phenomenon{id?,status?,name?,description?,ai_image?}, emotional_pulse, segments[{label,share,samples}], narrative_stack{l1,l2,l3}, danger?, summary{one_line,narrative_type}, battlefield{factions}, full_report?.
- Meta: analysis_version, analysis_build_id, analysis_is_valid, analysis_invalid_reason, analysis_missing_keys, match_ruleset_version, fingerprint_version, registry_version, phenomenon_status, phenomenon_case_id.
- Policy: phenomenon.id set only by enrichment/registry; analysis_json.phenomenon is descriptive; DB columns are SoT.
- Minimal skeleton:
```json
{
  "post": {"post_id":"...", "author":"...", "text":"...", "link":null, "images":[], "timestamp":"...", "metrics":{"likes":0,"views":null,"replies":null}},
  "phenomenon": {"id":null, "status":"pending", "name":null, "description":"..."},
  "emotional_pulse": {"primary": null, "cynicism": 0.0, "hope": 0.0, "outrage": 0.0, "notes": null},
  "segments": [],
  "narrative_stack": {"l1": null, "l2": null, "l3": null},
  "summary": {"one_line": null, "narrative_type": null},
  "battlefield": {"factions": []},
  "analysis_version": "v4",
  "analysis_build_id": "uuid",
  "analysis_is_valid": true
}
```

### 3. Phenomenon Identity & Registry
- Fingerprint: deterministic normalization of post_text + OCR artifact + reaction samples; cluster ordering by size desc then signature hash asc; case_id = sha256(fingerprint); constants FINGERPRINT_VERSION/MATCH_RULESET_VERSION/REGISTRY_VERSION = v1; mint uuid5 with invariant namespace.
- Enrichment: match-or-mint stub sets phenomenon_id/status/case_id and writes both analysis_json fields and threads_posts columns (SoT).
- Registry persistence: `narrative_phenomena` stores canonical rows; current code does not auto-populate names/descriptions. Backfill/migrations ensure rows exist for phenomenon_id values.

### 4. API Contracts (Backend → Frontend)
- GET /api/posts: list with post metadata + phenomenon_id/status/case_id/name (DB-first, fallback to analysis_json, default pending). Errors return JSON {detail, dev_context}.
- GET /api/analysis-json/{post_id}: returns analysis_json + phenomenon envelope {id,status,case_id,canonical_name,source}.
- GET /api/library/phenomena: registry browse with stats {id, canonical_name, description, status, total_posts, last_seen_at}.
- GET /api/library/phenomena/{id}: shelf {meta, stats{total_posts,total_likes,last_seen_at}, recent_posts[{id,created_at,snippet,like_count,phenomenon_status}]}.
- POST /api/library/phenomena/{id}/promote: provisional → active only.
- Debug: /api/debug/latest-post, /api/debug/phenomenon/backfill_from_json (patch columns from analysis_json).

### 5. Dataflow Summary
| Stage | Inputs | Outputs | Storage | Notes |
| --- | --- | --- | --- | --- |
| Crawler/Archive | threads HTML, metrics, comments, images | post_text, metrics, raw_comments, images | threads_posts | Raw SoT |
| Vision/OCR | images | VisionGate → Two-Stage (V1 classify, V2 extract if needed) | threads_posts.vision_* + images | used in fingerprint/enrich |
| Quant/Clustering | comments | cluster_summary, quant fields | threads_posts | deterministic |
| Analyst (LLM) | post + quant | analysis_json (AnalysisV4), full_report, meta | threads_posts.analysis_json | interpretive only |
| Enrichment | evidence fingerprint | phenomenon_id/status/case_id (deterministic) | threads_posts cols + analysis_json | SoT for identity |
| Registry | phenomenon_id | rows in narrative_phenomena | registry | definition authority |
| API | threads_posts (+ registry stats) | JSON responses | HTTP | DB-first identity |

### 6. Drift & Risks
- Missing registry rows for existing phenomenon_id values → empty library browse. Mitigation: sync/insert rows by id.
- Legacy posts with analysis_json phenomenon but null columns → pending status in API. Mitigation: backfill endpoint/SQL.
- Canonical names absent (registry not curated) → phenomenon_name null in API. Mitigation: governance populate registry.
- Fingerprint rule changes require version bump and coordinated backfill.
