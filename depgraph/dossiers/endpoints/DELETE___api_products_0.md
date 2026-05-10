---
node_id: DELETE::/api/products/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f2857bf92f8b0d4521870004ebf360dcf8bb5fbabf7f98f81412fdd5303d8c7f
status: llm_drafted
---

# DELETE /api/products/{product_id}

## Purpose

Deletes a specific product record from the database. This is a destructive operation used by administrators to remove inventory or items that are no longer relevant to an event. It is distinct from the `PUT` endpoint which updates product attributes; this method removes the record entirely.

## Invariants

- **HTTP Method/Path**: `DELETE /api/products/{product_id}`.
- **Auth Requirement**: Requires a valid session via `require_permission("events.edit")`.
- **Return Status**: Returns `204 No Content` on successful deletion.
- **Scope Enforcement**: Must pass `_require_event_org_scope` to ensure the user has permission to modify products within the specific event's organization.

## Gotchas

- **Cross-org security**: Per commit `058aa8c`, this endpoint relies on strict tier-C cross-org scope enforcement. If the `product_id` belongs to an event in a different organization, the request must fail via `_require_event_org_scope` to prevent unauthorized deletions.

## Cross-cutting concerns

- **Auth**: Depends on `require_permission("events.edit")`.
- **Audit**: N/A.
- **Side effects**: Deleting a product may impact the visibility of that product in the event's registration or merchandise lists.

## External consumers

- `concorda-web::src/lib/api.ts::adminProductsApi.delete`
