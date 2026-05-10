---
node_id: POST::/api/series
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ad2f48ca18eb5eb99b52fe2e97fbea6d3369dd19bc087e2d17d60d8c6ffb9fab
status: llm_drafted
---

# POST /api/series

## Purpose

Creates a new `Series` record and optionally associates it with specific Organizing Authorities (OAs). This endpoint is the primary way to initialize a racing season or competition structure. It is distinct from the `generate-races` endpoint, which expands an existing series' schedule into individual `Regatta` records.

## Invariants

- **HTTP Method:** `POST`.
- **Auth Requirement:** Requires a user with `_require_manager` privileges.
- **Scope Check:** Must pass `_require_oa_scope` for any provided `organizing_authority_uuids`.
- **Slug Generation:** Automatically generates a unique, URL-friendly slug via `_ensure_unique_slug` based on the provided name.
- **Return Shape:** Returns a `SeriesRead` object, which includes the generated `id` and `slug`.

## Gotchas

- **Manual Fallback Only:** Per the docstring in `generate_races`, this endpoint (and its related expansion logic) is a manual fallback for series created via the Admin UI. If a series is being imported via a bundle, use `scripts/season_bundle/upsert.py` instead; the importer is the authoritative source and handles child-record cleanup, whereas this endpoint's logic may lead to slug mismatches.
- **Slug Mismatch Risk:** Recent refactor `8652d95` and commit `8652d95` highlight concerns regarding how slugs are derived. Ensure any automated processes calling this endpoint account for the fact that `_generate_slug` is used to create the identity of the series.

## Cross-cutting concerns

- **Auth**: Uses `_require_manager` for the user and `_require_oa_scope` for the authority-specific access control.
- **Side effects**: Creating a series is the prerequisite for the `generate-races` expansion flow, which populates the `Regatta` table.

## External consumers

- `concorda-web::src/lib/api.ts::seriesApi.create`
