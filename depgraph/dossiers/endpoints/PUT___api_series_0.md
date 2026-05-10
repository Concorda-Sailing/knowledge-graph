---
node_id: PUT::/api/series/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 819cc7915c38d8dec7f865e32aa116d96ad0c95516033650e56f6639b74a35a5
status: llm_drafted
---

# PUT /api/series/{series_id}

## Purpose

Updates an existing Series record. It allows for modification of core series attributes (like `name`) and the management of `organizing_authority_uuids`. This is the primary method for administrative updates to a series via the web UI.

## Invariants

- **HTTP Method**: `PUT`.
- **Auth**: Requires a user with manager privileges via `_require_manager`.
- **Scope**: Must pass `_require_series_org_scope` and `_require_oa_scope` for any provided `organizing_authority_uuids`.
- **Slug Generation**: If the `name` is changed, the `slug` is automatically regenerated via `_ensure_unique_slug` to maintain URL consistency.
- **Return Shape**: Returns a `SeriesRead` model with the updated state.

## Gotchas

- **Slug Mismatch**: Per commit `8652d95`, there is a known mismatch between how this endpoint generates slugs (via `_generate_slug`) and how the `scripts/season_bundle/upsert.py` importer handles them (index-based). If a series was imported via a bundle, manual updates to the name via this endpoint may cause routing/lookup discrepancies.
- **Manual Fallback Only**: This endpoint is a manual fallback for series where the schedule was added via the admin UI. If a series was imported from a bundle, use the bundle importer instead of this endpoint to avoid orphaned or misaligned child records.

## Cross-cutting concerns

- **Auth**: Uses `_require_manager` and `_require_series_org_scope`.
- **Side effects**: Changing the `name` triggers a slug regeneration, which may affect any consumer relying on the series URL/slug.

## External consumers

- `concorda-web::src/lib/api.ts::seriesApi.update`

## Open questions

- Should the slug generation logic be standardized between this endpoint and the `upsert.py` bundle importer to prevent the mismatch identified in `8652d95`?
