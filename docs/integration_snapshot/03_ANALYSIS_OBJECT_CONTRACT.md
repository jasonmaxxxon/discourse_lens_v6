# analysis_json Contract (Current)

Derived from `analysis/schema.py`, `analysis/build_analysis_json.py`, `analysis/analyst.py`, frontend types `dlcs-ui/src/types/analysis.ts`.

## Top-Level Keys (AnalysisV4 payload)
- `post`: {`post_id`, `author`, `text`, `link`, `images[]`, `timestamp`, `metrics{likes,views,replies}`}
- `phenomenon`: {`id` (registry-owned, may be null/pending), `status` (pending/minted/matched/failed), `name` (optional legacy), `description` (interpretive), `ai_image`?}
- `emotional_pulse`: {`primary`?, `cynicism`, `hope`, `outrage`, `notes`?}
- `segments`: array of {`label`, `share` 0–1, `samples[]` with `comment_id`,`user`,`text`,`likes`, `linguistic_features`[]}
- `narrative_stack`: {`l1`,`l2`,`l3`} (strings; may be extracted from full_report)
- `danger`: {`bot_homogeneity_score`, `notes`} (optional)
- `full_report`: markdown text (optional)
- Compatibility wrappers:
  - `summary`: {`one_line`, `narrative_type`}
  - `battlefield`: {`factions`: mirrors `segments`}

## Meta Added During Persist
- `analysis_version` (string, e.g., "v4")
- `analysis_build_id` (uuid string)
- `analysis_is_valid` (bool), `analysis_invalid_reason`, `analysis_missing_keys`
- Optional: `match_ruleset_version`, `fingerprint_version`, `registry_version`, `phenomenon_status`, `phenomenon_case_id` (patched by async enrichment)

## Frontend Expectations (dlcs-ui)
- `AnalysisJson` type expects: `post_id`, `meta`, `summary`, `tone`, `strategies`, `battlefield`, `metrics`, `layers`, `discovery`, `raw_markdown`, `raw_json`.
- Normalizer (`normalizeAnalysisJson.ts`) maps narrative decks using `metrics`, `battlefield.factions`, `layers.l1/2/3`, `tone` fields.
- Phenomenon identity surfaced via `insight_deck.phenomenon.issue_id` built from post_id/sector_id; registry IDs not yet displayed in UI.

## JSON Skeleton Example
```json
{
  "post": {
    "post_id": "123",
    "author": "user",
    "text": "...",
    "link": "...",
    "images": ["..."],
    "timestamp": "2025-01-01T00:00:00",
    "metrics": { "likes": 10, "views": 100, "replies": 3 }
  },
  "phenomenon": {
    "id": null,
    "status": "pending",
    "name": null,
    "description": "...",
    "ai_image": null
  },
  "emotional_pulse": { "primary": null, "cynicism": 0.2, "hope": 0.1, "outrage": 0.3, "notes": null },
  "segments": [
    {
      "label": "Cluster 0",
      "share": 0.6,
      "samples": [
        { "comment_id": "c1", "user": "anon", "text": "...", "likes": 12, "linguistic_features": [] }
      ],
      "linguistic_features": []
    }
  ],
  "narrative_stack": { "l1": "...", "l2": "...", "l3": "..." },
  "danger": { "bot_homogeneity_score": 0.8, "notes": "..." },
  "summary": { "one_line": "...", "narrative_type": "..." },
  "battlefield": { "factions": [ { "label": "Cluster 0", "share": 0.6, "samples": [] } ] },
  "full_report": "...",
  "analysis_version": "v4",
  "analysis_build_id": "uuid",
  "analysis_is_valid": true
}
```

## Boundaries
- `phenomenon.id` is set only by registry/enrichment; Step3/LLM outputs are ignored for identity.
- Validation (`validate_analysis_json`) requires `post.id/text/timestamp` and either `phenomenon.id` or `phenomenon.name`; pending status bypasses name requirement.
- Registry counter: `narrative_phenomena.occurrence_count` (default 0) tracks match/mint usage via RPC `increment_occurrence(phenomenon_id uuid)` and is not part of `analysis_json`; callers should use the RPC to mutate counts.
- Ops pipeline completion gate: Pipeline A items only complete when `threads_posts.analysis_json` or `threads_posts.full_report` is non-null for the returned `post_id`; missing analysis causes job failure at analyst/store stage (ingest may still succeed).

## API Phenomenon Envelope (analysis-json endpoint)
- `/api/analysis-json/{post_id}` now returns a sibling `phenomenon` object:
  - `id`, `status`, `case_id`, `canonical_name`, `source` ("db_columns" | "analysis_json" | "default")
  - Merged with DB-first precedence; `analysis_json` remains unchanged for backward compatibility.
