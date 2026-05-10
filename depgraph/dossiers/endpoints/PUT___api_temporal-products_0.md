---
node_id: PUT::/api/temporal-products/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 31a2002802d49995b249860edddaebacfd41a005ea2696b9b9f3f76e560afd02
status: llm_drafted
---

# PUT /api/temporal-products/{product_id}

## Purpose

Provides administrative control over `TemporalProduct` entities, specifically for updating, deleting, and duplicating products across different years. This endpoint is the primary way to manage the lifecycle of products that are tied to specific timeframes (years) and their associated merchandise. It is distinct from standard product management as it handles the specific logic of year-based uniqueness and merchandise association.

## Invariants

- **Requires `admin.memberships.manage` permission** via the `require_permission` dependency.
- **`PUT /{product_id}` enforces uniqueness** on the combination of `slug` and `year`.
- **`DELETE /{product_id}` performs a cascading cleanup** of `TemporalProductMerchandise` entries before deleting the product.
- **`POST /{product_id}/duplicate` requires a `target_year`** as a query parameter to define the new product's temporal context.
- **Returns `TemporalProductRead` shape** on successful `PUT` or `POST` operations.

## Gotchas

- **Uniqueness constraint collision:** If an update changes a `slug` or `year`, the API checks for existing products with that same slug/year combination to prevent duplicates. This is a hard check in the `update_temporal_product` function to prevent invalid state.
- **Manual merchandise cleanup required:** The `delete_temporal_product` function explicitly deletes from `TemporalProductMerchandise` before the product itself is removed. Failure to do this manually in the logic (if the DB doesn't have a foreign key cascade) would leave orphaned records.

## Cross-cutting concerns

- **Auth**: Requires `admin.memberships.manage` permission.
- **Rate limit**: See commit `ec53704` regarding security hardening on auth/write endpoints; ensure any high-frequency administrative automation respects these limits.
- **Side effects**: Updates to these products may affect the visibility of seasonal merchandise in the storefront/dashboard.

## External consumers

- `concorda-web::src/lib/api.ts::adminTemporalProductsApi.update` (Internal web admin interface).
