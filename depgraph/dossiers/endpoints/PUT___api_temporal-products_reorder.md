---
node_id: PUT::/api/temporal-products/reorder
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 557d6760b1ce9dec4d19073ccdc358537447ae06747c47983f29b28d1fdbd4a5
status: current
---

# PUT /api/temporal-products/reorder

## Purpose

Updates the display order of `TemporalProduct` entities via a list of IDs. This is used to persist the state of drag-and-drop reordering interfaces in the admin dashboard. It is distinct from `update_temporal_product` because it performs a bulk update on the `sort_order` attribute based on the list index rather than updating specific product fields.

## Invariants

- **HTTP Method is `PUT`**.
- **Requires `admin.memberships.manage` permission** via the `require_permission` dependency.
- **Input is a `ReorderRequest`** containing a `ids: list[str]` field.
- **Updates `product.sort_order`** to the current index of the ID in the provided list.
- **Non-existent IDs are silently ignored** during the loop; the function does not throw if a provided ID is not found in the database.

## Gotchas

- **Order is index-dependent.** The `sort_order` is set directly to the `enumerate` index. If the client sends a list with gaps or non-sequential indices, the database state will reflect that specific list order.
- **Recent security hardening.** Per commit `ec53704`, ensure that any changes to this endpoint do not bypass the `require_permission` check, as the system is actively tightening unauthenticated or unauthorized DB write access.

## Cross-cutting concerns

- **Auth**: Requires `admin.memberships.manage`.
- **Rate limit**: None explicitly defined for this endpoint, but subject to general API rate-limiting policies.
- **Audit**: N/A.
- **Side effects**: Reordering affects the visual sequence of products in the admin management dashboard.

## External consumers

- `concorda-web` (via `adminTemporalProductsApi.reorder`).
