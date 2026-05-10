---
node_id: GET::/api/temporal-products
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b74baba6339c1c4a6468d3b6d59ffd52265f7f463607337701b4170d55dd048d
status: llm_drafted
---

# GET /api/temporal-products

## Purpose

Provides an administrative interface for managing temporal products (e.g., seasonal membership or event-specific pricing). It allows for listing, filtering by year/category, and reordering products via a drag-and-drop compatible endpoint. This is distinct from standard product endpoints as it handles the automatic generation of yearly product cycles.

## Invariants

- **Requires `admin.memberships.view` permission** for GET requests on the collection and specific product lookups.
- **Requires `admin.memberships.manage` permission** for POST and PUT (reorder) operations.
- **Returns a list of `TemporalProductRead` objects** when querying the collection.
- **Automatic product generation:** If a query for a specific `year` and `category` returns zero results, the system automatically triggers `_copy_products_from_previous_year` to ensure the temporal cycle is populated.

## Gotchas

- **Automatic creation side-effect:** Calling `GET /api/temporal-products` with a `year` and `category` that has no data will trigger a database write via `_copy_products_from_previous_year`. This makes a "read" operation potentially state-changing in the absence of data.
- **Ordering logic:** The `reorder_products` endpoint (PUT `/reorder`) relies on the client providing a full list of IDs to correctly update the `sort_order` integer.

## Cross-cutting concerns

- **Auth**: Requires `admin.memberships.view` for GET and `admin.memberships.manage` for POST/PUT.
- **Rate limit**: None explicitly defined for this endpoint, but see commit `ec53704` regarding general auth/DB write security hardening.
- **Audit**: N/A.

## External consumers

None known.
