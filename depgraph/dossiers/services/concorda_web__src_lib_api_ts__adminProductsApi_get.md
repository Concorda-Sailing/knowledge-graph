---
node_id: concorda-web::src/lib/api.ts::adminProductsApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2914235cb4004988782bb1c4e213d1de11c61776b4302fc44db4ca9eab20c1f6
status: current
---

# adminProductsApi.get

## Purpose

Provides the administrative interface for managing product lifecycle and metadata. It handles CRUD operations for products, including memberships and event-specific offerings. Use this service when an administrative action (creating, updating, or deleting a product) is required, rather than fetching public-facing product data.

## Invariants

- **Uses `fetchApiAuthenticated`** — all methods require a valid session/bearer token to execute.
- **`list` method supports filtering** — `event_id` and `include_inactive` are the only supported query parameters.
- **`get` returns a single `Product` object** — expects a specific ID and returns the full object shape.
- **`create` and `update` expect specific types** — `create` uses `ProductCreate` and `update` uses `ProductUpdate` to ensure payload integrity.

## Gotchas

- **`list` vs `get` behavior** — the `list` method is the primary way to filter products by `event_id` to ensure an admin is looking at the correct context for a specific regatta or event.
- **Product Category constraints** — `ProductCategory` is strictly limited to `"Membership"` or `"Event"`. Attempting to pass other strings will fail at the API level.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level permissions).
- **Side effects**: Updates to products via `create` or `update` will affect the availability and pricing of items displayed in the user-facing registration flows.

## External consumers

None known.
