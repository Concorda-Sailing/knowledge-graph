---
node_id: POST::/api/temporal-products/duplicate-year
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a5d341d8492ccccbcdeda736c4e8d4a361c23d72fde67da6d2ebc60df06563d7
status: current
---

# POST /api/temporal-products/duplicate-year

## Purpose

The endpoint duplicates all `TemporalProduct` records from a `source_year` to a `target_year`. It is used by administrators to rapidly scaffold a new season's product lineup by copying names, slugs, descriptions, prices, and merchandise associations from the previous year. This is a bulk operation intended to save manual entry time during seasonal transitions.

## Invariants

- **Requires `admin.memberships.manage` permission** via the `require_permission` dependency.
- **Target year must be empty.** If any `TemporalProduct` already exists for the `target_year`, the request fails with a 400 error to prevent accidental overwrites.
- **Source year must contain products.** If no products are found for the `source_year`, the request fails with a 404.
- **Returns a list of `TemporalProductRead` objects.** The response includes the newly created products with their updated `year` and `start_date`/`end_date` values.
- **Merchandise associations are preserved.** The function calls `_set_merchandise_for_product` to link the new products to the same merchandise IDs as the source.

## Gotchas

- **Atomic failure on empty source.** If the `source_year` has no products, the entire operation fails; this is not a "create empty year" tool, but a "copy existing data" tool.
- **Manual cleanup required for collisions.** Because the endpoint throws a 400 if the `target_year` is not empty, an admin must manually delete existing products for that year before calling this endpoint.

## Cross-cutting concerns

- **Auth**: Requires `admin.memberships.manage` permission.
- **Rate limit**: None (Note: `ec53704` fixed rate limits on auth endpoints, but this is a protected admin-only route).
- **Side effects**: Rebuilds the product catalog for the target year, which may affect any UI components displaying seasonal product lists or registration forms.

## External consumers

None known.
