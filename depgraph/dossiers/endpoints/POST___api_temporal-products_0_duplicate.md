---
node_id: POST::/api/temporal-products/{0}/duplicate
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cdff4b302c53084ed63893ca0db7b656394f578dc621bcb55e80d4f5f1e7dc40
status: current
---

# POST /api/temporal-products/{product_id}/duplicate

## Purpose

Creates a copy of a specific `TemporalProduct` for a new target year. This is used to propagate product configurations (name, slug, price, category, etc.) across seasons while allowing for year-specific adjustments. It is distinct from `duplicate_year`, which is a bulk operation for an entire year's set.

## Invariants

- **Requires `admin.memberships.manage` permission** via the `_user` dependency.
- **Input `product_id` must exist**; otherwise, returns a 404.
- **Target year must be unique for the product slug.** If a product with the same slug already exists in the `target_year`, the request returns a 400.
- **Returns `TemporalProductRead` shape.** The response is a serialized version of the newly created product.
- **Merchandise associations are cloned.** The function calls `_set_merchandise_for_product` to ensure the new product inherits the same merchandise IDs as the original.

## Gotchas

- **Manual date calculation.** The function relies on `_year_to_dates(target_year)` to generate the `start_date` and `end_date`. If the logic in `_year_to_dates` is incorrect, the product will have an invalid temporal window for that year.
- **Bulk duplication collision.** If using the sibling `duplicate_year` endpoint, the user must ensure the target year is empty first, as the API explicitly checks `existing_count > 0` and throws a 400 to prevent accidental overwrites.

## Cross-cutting concerns

- **Auth**: Requires `admin.memberships.manage` permission.
- **Rate limit**: none.
- **Side effects**: Creates a new `TemporalProduct` record and associated `TemporalProductMerchandise` links in the database.

## External consumers

None known.
