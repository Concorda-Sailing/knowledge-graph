---
node_id: DELETE::/api/temporal-products/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6b546bbb4d8dec085dd6c920abf25c6d5c8dbe39615624e18b42611eea0e6d8e
status: llm_drafted
---

# DELETE /api/temporal-products/{product_id}

## Purpose

Permanently removes a `TemporalProduct` from the database. This is an administrative action used to prune outdated or incorrect product entries that are no longer needed for a specific year. It is distinct from the `duplicate` endpoint, which preserves the product structure by creating a new instance for a different year.

## Invariants

- **HTTP Method/Path**: `DELETE /api/temporal-products/{product_id}`.
- **Auth**: Requires `admin.memberships.manage` permission via the `require_permission` guard.
- **Return Shape**: Returns `204 No Content` on success.
- **Cleanup**: Automatically deletes all associated `TemporalProductMerchandise` records to prevent orphaned links in the join table.

## Gotchas

- **Manual cleanup required**: The function explicitly deletes `TemporalProductMerchandise` entries before deleting the product itself. If a new association type is added to `TemporalProduct` in the future, it must be manually added to this deletion logic to avoid foreign key violations.
- **Admin-only access**: Per the `_user` dependency, this endpoint is strictly protected. Attempting to call this without the `admin.memberships.manage` permission will result in a 403/401 error.

## Cross-cutting concerns

- **Auth**: Uses `require_permission("admin.memberships.manage")`.
- **Rate limit**: None (though the file as a whole is subject to the security fixes in commit `ec53704`).
- **Side effects**: Deleting a product will remove it from the visibility of the registration system and any active schedules/event lists that reference this product ID.

## External consumers

- `concorda-web::src/lib/api.ts::adminTemporalProductsApi.delete`
