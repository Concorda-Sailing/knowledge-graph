---
node_id: GET::/api/temporal-products/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e3587ed46fec506acb6e09f352aafe421661cf21a5d8d7587986b3e0c03fd0be
status: current
---

# GET /api/temporal-products/{product_id}

## Purpose

Fetches a single `TemporalProduct` by its unique ID. This endpoint is used by the admin dashboard to display the details of a specific product (like a seasonal merchandise bundle) that is tied to a specific year and slug. It is the read-only counterpart to the `POST` and `PUT` methods in this router, used when an admin needs to view or edit a specific product's configuration.

## Invariants

- **Requires `admin.memberships.view` permission** via the `require_permission` dependency.
- **Returns a `TemporalProductRead` model.** The response includes the full product details, including its associated merchandise.
- **Throws 404 if the ID is invalid.** If the `product_id` does not exist in the database, the API returns a 404 error rather than a null object.
- **Input is a string-based `product_id`.**

## Gotchas

- **Strict permission check.** Unlike general product lookups, this requires the `admin.memberships.view` permission; if the user has general product access but not membership-specific admin access, this will fail.

## Cross-cutting concerns

- **Auth**: Requires `admin.memberships.view` permission.
- **Rate limit**: None (per `ec53704`, rate limits are primarily enforced on auth endpoints, but this is a protected admin-only route).
- **Side effects**: Used by the admin interface to populate the detail view for seasonal product management.

## External consumers

- `concorda-web::src/lib/api.ts::adminTemporalProductsApi.get`
