---
node_id: POST::/api/series/{0}/generate-races
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1f8e1f408ce5e0c7404ec98eb350ea93688fc537cba19bf124d92a8b4744a0f6
status: current
---

# POST /api/series/{series_id}/generate-races

## Purpose

Converts a `Series`'s `race_schedule` (a list of JSON objects) into individual `Regatta` records. This is a manual fallback for series where the schedule was added via the admin UI rather than a bundle import. It expands the high-level series data into granular, editable regatta entries with their own slugs and dates.

## Invariants

- **Requires `_require_manager`** — the caller must be authenticated as a manager of the organization.
- **Requires `_require_series_org_scope`** — ensures the user has permission to modify the specific series.
- **Input is `series_id`** — the path parameter must be a valid UUID for an existing Series.
- **`race_schedule` must be non-empty** — if the series has no schedule, the endpoint returns a 400 error.
- **Output is a list of `Regatta` objects** — specifically, it returns the first newly created/processed regatta from the expansion.

## Gotchas

- **Importer precedence** — per source comment, the bundle importer in `scripts/season_bundle/upser.py` uses index-based slugs (`{slug}-r{idx:02d}`). If a series was imported from a bundle, do not use this endpoint to manage it; use the importer instead, as this endpoint will not clean up or reconcile children created by the importer.
- **Slug mismatch risk** — per commit `8652d95`, there is a known pattern of slug mismatching when generating names. This endpoint uses `_generate_slug` and `_ensure_unique_slug` to mitigate this, but manual intervention may be needed if the series name changes after generation.
- **Date parsing fragility** — the endpoint attempts to parse `race_date` as an ISO string, falling back to `%Y-%m-%d`. If the date format in the `race_schedule` is malformed, the entry is silently skipped (incrementing `skipped`) rather than failing the whole request.

## Cross-cutting concerns

- **Auth**: Requires `_require_manager` and `_require_series_org_scope`.
- **Side effects**: Creates `Regatta` records which are the primary entities for the schedule detail pages and event-based views.

## External consumers

- `concorda-web::src/lib/api.ts::seriesApi.generateRaces`

## Open questions

- Should the endpoint return the full list of created/skipped counts to the client, or is the single-object return sufficient for the current UI implementation?
