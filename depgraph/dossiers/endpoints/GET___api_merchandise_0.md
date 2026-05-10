---
node_id: GET::/api/merchandise/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6160f1f106520b9350c919438e4c6568e8c3e9768d953ecfc30a0f3cff8f314c
status: llm_drafted
---

# GET /api/merchandise/{item_id}

## Purpose

Retrieves a single merchandise item by its unique ID. This is a read-only endpoint used by the admin dashboard to display detailed product information. It is distinct from the collection endpoint (GET `/api/merchandise`) which returns a list of items filtered by activity status.

## Invariants

- **Requires `admin.memberships.view` permission** via the `require_permission` dependency.
- **Returns a `MerchandiseRead` object** containing the full item details.
- **Throws a 404 error** if the provided `item_id` does not exist in the database.
- **Uses a string-based `item_id`** for the lookup.

## Gotchas

- **Permission mismatch:** Ensure the caller has `admin.memberships.view` rather than just general access. If an agent attempts to use a lower-tier permission, the request will fail at the dependency injection level before reaching the function body.

## Cross-cutting concerns

- **Auth**: Requires `admin.memberships.view` permission.
- **Side effects**: None.

## External consumers

- `concorda-web::src/lib/api.ts::adminMerchandiseApi.get`
