---
node_id: concorda-web::src/lib/api.ts::adminMerchandiseApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3064cdf54194a1c71205bbb33291eba0dd824a3f760acb9fcdca0e4e7f645151
status: current
---

# adminMerchandiseApi.list

## Purpose

Provides an interface for managing organization-wide merchandise (products). It handles fetching, creating, updating, and deleting merchandise items via the `/api/merchandise` endpoint. Use this when building administrative views for product catalogs, such as the category-based product pages or the main merchandise dashboard.

## Invariants

- **Method is `GET` for `list`** — uses an optional `include_inactive` query parameter to filter visibility.
- **Requires `fetchApiAuthenticated`** — all methods rely on a valid bearer token; unauthenticated calls will fail.
- **Returns `Merchandise[]` for `list`** — the response is a collection of product objects.
- **`create` and `update` expect JSON bodies** — the `data` argument must match the `MerchandiseCreate` or `MerchandiseUpdate` interface shapes.

## Gotchas

- **`include_inactive` is a string-based query param** — the `list` method explicitly sets the value to `"true"` in the URL string if requested; ensure any manual URL construction matches this pattern.
- **Dependency on `fetchApiAuthenticated`** — if the authentication layer changes (e.g., moving from bearer tokens to session cookies), this entire object must be audited.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level permissions).
- **Side effects**: Updates to this API affect the product displays on `CategoryProductsPage` and the main `MerchandisePage`.

## External consumers

- None known.
