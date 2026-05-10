---
node_id: DELETE::/api/regattas/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f696796282bfd31a46bd8ca6c092926558ae73bada13ff19c0935fe0156ef68b
status: llm_drafted
---

# DELETE /api/regattas/{regatta_id}

## Purpose

Deletes a specific regatta from the database. This is a destructive operation used by administrators to remove regattas that are no longer relevant or were created in error. It is distinct from updating a regatta's configuration; it is a permanent removal of the record.

## Invariants

- **HTTP Method/Status**: `DELETE` with a `204 No Content` success status.
- **Auth Guard**: Requires a user authenticated via `_require_manager`.
- **Scope Enforcement**: Must pass `_require_regatta_org_scope` to ensure the user has authority over the specific organization the regatta belongs to.
- **Return Shape**: Returns no body on success.

## Gotchas

- **Security/Scope**: Per commit `058aa8c`, this endpoint enforces tier-C cross-org scope. A user might be a manager in one organization but will receive a 403/404 if attempting to delete a regatta belonging to a different organization.
- **Dependency on `_require_regatta_org_scope`**: If the scope check fails, the client receives a 404 or 403 depending on the internal implementation of the guard, preventing unauthorized deletions.

## Cross-cutting concerns

- **Auth**: Uses `_require_manager` and `_require_regatta_org_scope`.
- **Side effects**: Deleting a regatta will cause the "regatta count" or "event list" in the dashboard/schedule views to decrement.

## External consumers

- `concorda-web::src/lib/api.ts::regattaApi.delete`

## Open questions

- None.
