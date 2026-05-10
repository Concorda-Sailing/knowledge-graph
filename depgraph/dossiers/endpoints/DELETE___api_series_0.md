---
node_id: DELETE::/api/series/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c18208253fa19676bed6f29116344a461eb21e743e26a9fdbd0b5c2c92b64efe
status: llm_drafted
---

# DELETE /api/series/{series_id}

## Purpose

Deletes a specific series from the database. This is a destructive operation used to remove entire series-level structures, distinct from deleting individual races or events. It is the final step in a series lifecycle and should only be called when the entire series context is no longer required.

## Invariants

- **HTTP Method is `DELETE`** with a `204 No Content` success status.
- **Requires `series_id`** as a path parameter.
- **Strictly enforces `_require_manager`** via the `current_user` dependency.
- **Enforces organizational scope** via `_require_series_org_scope` before execution.
- **Returns no body** on success; failure to find the series results in a `404 Not Found`.

## Gotchas

- **Tier-C scope enforcement is mandatory.** Per commit `058aa8c`, this endpoint relies on `_require_series_org_scope` to prevent cross-org deletion attempts; ensure any modifications to the deletion logic maintain this guard to prevent unauthorized data destruction.
- **Deletion is permanent.** There is no "soft delete" or "archive" state implemented for series; once `db.commit()` executes, the series and its associated data are removed from the database.

## Cross-cutting concerns

- **Auth**: Requires a valid session and must pass the `_require_manager` check.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Deleting a series will orphan or impact any downstream race/event data that relies on this `series_id` for relational integrity.

## External consumers

- `concorda-web::src/lib/api.ts::seriesApi.delete`
