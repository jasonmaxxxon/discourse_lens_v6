# Change Impact Checklist (Phenomenon Identity)

If modifying phenomenon_id/status/case_id or registry wiring, update:

- **Python Modules**
  - `analysis/phenomenon_fingerprint.py`: fingerprint_version, namespace, ordering rules.
  - `analysis/phenomenon_enricher.py`: patch guard, metadata keys (match_ruleset_version, registry_version), feature flag.
  - `analysis/build_analysis_json.py`: phenomenon block construction; ensure identity remains registry-owned.
  - `analysis/analyst.py`: enrichment submission hook; pending status tagging.
  - `database/store.py`: if writing `phenomenon_id` to `threads_posts`.
- **Endpoints**
  - `/api/analysis-json/{post_id}` (`webapp/main.py`) if response should expose new identity fields.
  - `/api/posts` if listing needs phenomenon status/ID badges.
- **DB Tables/Columns**
  - `threads_posts.phenomenon_id` (optional FK) and any new status columns.
  - Registry tables: `narrative_phenomena`, aliases, relations; RPC `match_phenomena`.
- **Frontend Touchpoints**
  - `dlcs-ui/src/types/analysis.ts` and normalizers if exposing phenomenon_id/status.
  - UI components consuming `analysis_json` (e.g., `NarrativeDetailPage`, `DiscoveryCard`) for new badges/states.

If you add a new column:
- Add to Supabase migrations.
- Update `webapp/main.py` selects/updates where relevant.
- Thread through `analysis/analyst.py` write payload.
- Extend frontend types/props where displayed.

Validation safety:
- Identity must remain deterministic; avoid letting LLM outputs set IDs.
- Enrichment retries should remain idempotent (case_id/uuid5).
