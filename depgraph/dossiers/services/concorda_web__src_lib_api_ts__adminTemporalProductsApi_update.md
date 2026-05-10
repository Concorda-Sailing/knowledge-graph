---
node_id: concorda-web::src/lib/api.ts::adminTemporalProductsApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9e0741c3acd701c654737045a5df27a154b033218fa3e8913376d0a21213f2ee
status: current
---

# adminTemporalProductsApi.update

## Purpose

Provides the API interface for updating existing `TemporalProduct` resources. It is used by administrative interfaces to modify product details or reorder product sequences. Use this method when a user-initiated change to a product's properties or position is required.

## Invariants

- **Method is `PUT`** — Uses the `PUT` verb to ensure idempotent updates to the resource.
- **Path includes ID** — The endpoint follows the pattern `/api/temporal-products/${id}`.
- **Requires `TemporalProductUpdate`** — The `data` payload must match the `TemporalProductUpdate` interface to ensure all fields are correctly serialized.
- **Returns full object** — On success, returns the updated `TemporalProduct` object.

## Gotchas

- **Reordering via `reorder`** — While `update` handles property changes, the `reorder` sibling method must be used for bulk ID-based sequence changes.
- **Dependency on `fetchApiAuthenticated`** — Like all methods in this service, this requires a valid bearer token; failure to authenticate will result in a 401/403 error.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the request is authorized.
- **Side effects**: Updates to this endpoint affect the `CategoryProductsPage` (specifically `page.tsx:234`) by changing the visible product data in the admin dashboard.

## External consumers

- `CategoryProductsPage` in the admin members module.
