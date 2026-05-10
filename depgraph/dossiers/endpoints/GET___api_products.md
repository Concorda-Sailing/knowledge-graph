---
node_id: GET::/api/products
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7a008f508421e40da0f3ebb5e38add251b88eb5c3287a7c5f0d49e79957355ce
status: current
---

# GET /api/products

## Purpose

Provides CRUD operations for products associated with specific events. It allows for listing, retrieving, creating, and updating product entities, which are used to manage event-specific commerce or inventory. Use this endpoint when you need to manage items that are scoped to an event, rather than global organization-level merchandise.

## Invariants

- **Requires `events.edit` permission** — All endpoints in this router (GET, POST, PUT) depend on the `require_permission("events.edit")` guard.
- **`GET /` filters by `event_id`** — If an `event_id` is provided, the result set is strictly limited to products belonging to that event.
- **`include_inactive` defaults to `False`** — By default, the list view excludes products where `is_active` is false to prevent accidental display of retired products.
- **Slug uniqueness is scoped to `event_id`** — The `create_product` method enforces that a product's `slug` must be unique within the specific event, not globally.
- **Returns `ProductRead` schema** — All responses follow the `ProductRead` model to ensure consistent field-level visibility.

## Gotchas

- **Cross-org scope enforcement** — Per commit `058aa8c`, products are strictly bound to the event's organization. The `_require_event_org_scope` check is critical during creation to prevent users from injecting products into events they do not own/manage.
- **Ordering is driven by `sort_order`** — The `list_products` endpoint defaults to `Product.sort_order`. If products appear in an unexpected sequence in the UI, check the integer value of the `sort_order` field in the database.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission via `require_permission`.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: Changes to products (via POST/PUT) may affect the visibility of items in the event's registration or payment flows.

## External consumers

None known.
