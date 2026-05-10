---
node_id: GET::/api/series/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0d8456177789f72ec7e4a9e6098c43b28ecb419509ef6b5b635e24126bcf8bd8
status: current
---

# GET /api/series/{series_id}

## Purpose

Retrieves a single `Series` object by its unique identifier. This is the primary endpoint for fetching the metadata and configuration of a specific racing series. It is distinct from `list_series`, which returns the full collection, and `update_series`, which is used for modifications.

## Invariants

- **Returns `SeriesRead` shape.** The response includes the base series data plus any attached Organizing Authority (OA) metadata via `_attach_oas`.
- **Throws 404 if not found.** If the `series_id` does not exist in the database, the API returns a `404` with the detail `"Series not found"`.
- **Uses `Series.id` for lookup.** The lookup is performed via a direct equality filter on the primary key.

## Gotchas

- **Slug mismatch for imported series.** Per the docstring in `generate_races`, if a series was created via the `scripts/season_bundle/upsert.py` importer, it uses index-based slugs (e.g., `{slug}-r01`). If you attempt to use the `generate-races` logic on these series, the resulting child regattas will have different slug patterns than the authoritative importer.
- **Manual fallback only.** This endpoint (and the associated `generate-races` path) is intended as a manual fallback for series created via the Admin UI; do not rely on it for automated bulk-import workflows.

## Cross-cutting concerns

- **Auth**: Requires `_require_manager` for write-adjacent operations (though this specific GET endpoint is public, its sibling `update_series` and `generate_races` enforce strict manager/scope checks).
- **Side effects**: Changes to series metadata or name (via `update_series`) trigger a slug regeneration via `_ensure_unique_slug`.

## External consumers

- `concorda-web::src/lib/api.ts::seriesApi.get` (used for rendering series detail pages).
