---
node_id: GET::/api/persons
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1546bf30128bb3dc41a8a59bbb55c6d0a625720f2db7b35a2ce7ccfd2ce80410
status: llm_drafted
---

# GET /api/persons

## Purpose

Retrieves a list of persons, either filtered by membership type or via a public-facing directory. The base endpoint (`GET /api/persons`) is a high-privilege administrative tool for listing all persons in the system, whereas the `/directory` sub-path is a specialized, lower-privilege view for members. Use the base endpoint for administrative management and the `/directory` endpoint for UI components that need to respect user privacy settings (e.g., hiding email/phone).

## Invariants

- **Base endpoint requires `_require_admin`** — access is restricted to `org_admin` or `system_admin` roles.
- **`/directory` endpoint requires `require_auth`** — any authenticated user can access it, but visibility is gated by person-level preferences.
- **Pagination is mandatory** — `skip` and `limit` parameters prevent unbounded result sets.
- **Output shape for `/directory` is `PersonDirectory`** — this includes a calculated `has_boat_management` flag and respects `show_email`/`show_phone` preference toggles.
- **Ordering is deterministic** — results are ordered by `last_name` then `first_name`.

## Gotchas

- **PII Leakage Risk** — per commit `33a37a3`, this module was the site of a security fix to close PII/privilege gaps. Ensure that `PersonDirectory` logic (specifically `dir_prefs.get("show_email")`) is never bypassed when adding new fields, as anonymous scrapers must not be able to access contact info.
- **Boat Management Eligibility** — the `has_boat_management` flag is calculated via a specific join on `TemporalProduct.grants_boat_management == True`. Per commit `8f94a94`, this is a critical field for the co-owner invite UI to gate actions.
- **SQL Boolean Comparison** — the join on `grants_boat_management` uses a manual comparison (`== True`) to satisfy the engine; do not rely on implicit truthiness for this specific column.

## Cross-cutting concerns

- **Auth**: Base endpoint uses `_require_admin` (`org_admin` or `system_admin`); `/directory` uses `require_auth`.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: The `has_boat_management` flag is used by the co-owner invite UI to gate the "invite" action.

## External consumers

None known.
