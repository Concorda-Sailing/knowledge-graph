---
node_id: GET::/api/series
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 889e7bedc4e6016a169d42d9fe7418530a01c3b2601c12d2c66641429c0fe416
status: llm_drafted
---

# GET /api/series

## Purpose

Provides the primary interface for managing "Series" (collections of regattas/events). It handles fetching the full list of series, retrieving specific series by ID, and creating/updating series with associated Organizing Authorities (OAs). Use this endpoint when you need to manage the high-level container that groups multiple racing events together.

## Invariants

- **`GET /api/series`** returns a list of `SeriesRead` objects, which includes the `organizing_authorities` array for each series.
- **`POST /api/series`** requires a `current_user` with `_require_manager` privileges.
- **`PUT /api/series/{series_id}`** requires both `_require_manager` and `_require_series_org_scope` to ensure the user has authority over the specific series being modified.
- **Slug generation** is automatic and derived from the `name` field via `_generate_slug`.
- **`_attach_oas`** is called on all return paths to ensure the `organizing_authorities` relationship is hydrated in the response.

## Gotchas

- **Slug mismatch with bundle importer:** Per the docstring in `generate_races`, the `_generate_slug` function used here produces different patterns than the `scripts/season_bundle/upsert.py` importer (which uses `{slug}-r{idx:02d}`). If a series was created via a bundle, do not use the `generate-races` endpoint to expand it, as the importer is the authoritative source for those children.
- **Manual vs. Automated expansion:** The `generate_races` endpoint is a manual trigger to expand a `race_schedule` into individual `Regatta` records. If you are automating series creation, prefer the bundle-based ingestion path to avoid inconsistent slugging.

## Cross-cutting concerns

- **Auth**: Uses `_require_manager` for write operations and `_require_oa_scope` to validate authority over specific Organizing Authorities.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Calling `generate_races` creates new `Regatta` records in the database.

## External consumers

- `concorda-web::src/lib/api.ts::seriesApi.list` (used for the series listing view).
