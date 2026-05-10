---
node_id: GET::/api/products/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: aa13dabe0d5c4110f0846f314827ab71f2623d279cb0a7c9a7f3f2434e748766
status: current
---

# GET /api/products/{product_id}

## Purpose

Fetches a single product by its unique ID. This is a read-only endpoint used primarily by administrative interfaces to display product details. It is distinct from the list endpoint (which supports filtering by `event_id` and `is_active`) as it provides a direct lookup via `product_id`.

## Invariants

- **HTTP Method: `GET`**
- **Path: `/api/products/{product_id}`**
- **Returns `ProductRead` shape.**
- **Requires `events.edit` permission.** Access is guarded by `require_permission("events.edit")`.
- **Returns 404 if not found.** If the `product_id` does not exist in the database, the API raises an `HTTPException` with status 404.

## Gotchas

- **Strict Permission Requirement:** Unlike some read-only endpoints, this requires the `events.edit` permission via the `_user` dependency. A user with only "view" permissions will fail to retrieve product details.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission via `require_permission`.
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: N/A

## External consumers

- `concorda-web::src/lib/api.ts::adminProductsApi.get`
