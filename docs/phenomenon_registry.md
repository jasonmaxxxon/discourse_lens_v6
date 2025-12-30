## CDX-044.1 — Deterministic Phenomenon System

This document summarizes the deterministic Match-or-Mint flow introduced in CDX-044.1.

### Phases
- **Phase 1 (sync, UI-critical)**: crawler + quant only. No blocking LLM calls. UI can render clusters/samples immediately.
- **Phase 2 (async enrichment)**: deterministic fingerprint → match-or-mint → L1–L3 interpretation. Runs in a background thread; pipeline responses are not blocked.

### Deterministic Evidence Fingerprint
Implemented in `analysis/phenomenon_fingerprint.py`.
- Normalization: NFC, strip BOM, collapse whitespace, trim, lowercase, optional truncation.
- Cluster ordering: size DESC, then `cluster_signature_hash` ASC (hash of top-M like_count samples).
- Reaction sampling: top1 per ordered cluster + global topK by like_count, deduped by normalized text.
- Fingerprint template:
```
TRIGGER:
{normalized post_text}

ARTIFACT:
{normalized ocr_text}

REACTIONS:
{normalized samples}
```
- `case_id = sha256(fingerprint)` guarantees idempotency for identical inputs.

### Phenomenon Registry
Schema in `database/migrations/2025-phenomenon-registry.sql`:
- `create extension vector;` must run first
- `narrative_phenomena` (canonical row, status, embedding, minted_by_case_id, occurrence_count; `id` provided by system, no default)
- Aliases + relations tables
- Optional `threads_posts.phenomenon_id` FK for report rows.
- RPC `match_phenomena(query_embedding, match_threshold, match_count)` for future vector matches.

### Async Match-or-Mint
Implemented in `analysis/phenomenon_enricher.py`.
- Non-blocking `ThreadPoolExecutor`; controlled by `ENABLE_PHENOMENON_ENRICHMENT` (default **off**, set `1` to enable).
- Builds evidence bundle → deterministic uuid5 mint (stub) using invariant namespace `NAMESPACE_UUID` → patches `analysis_json.phenomenon.id/status` and stores `phenomenon_case_id/match_ruleset_version/fingerprint_version/registry_version`.
- Ready to be swapped with vector search + Librarian agent without changing the call sites.

### Analysis JSON updates
- `Phenomenon` now carries `id`, `status` in addition to legacy name/description.
- Validation accepts `phenomenon_id` or `status=pending` to avoid failing when LLM text is omitted.
- Pipeline writes `analysis_json` immediately, then enrichment updates `phenomenon.id/status` asynchronously.

### Determinism Guarantees
- Same inputs → same normalized text → same fingerprint → same `case_id` and minted `phenomenon_id`.
- No randomness: clustering order, sample selection, hashing, and UUID minting are all deterministic.
- Versioned constants (`FINGERPRINT_VERSION`) gate behavior for future changes.
