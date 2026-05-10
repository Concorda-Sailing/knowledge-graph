---
node_id: POST::/api/products
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e6bfd7c3a423d5f3e9286ac700bb4576d25c60a0e8369298b5ed4a17d6490d48
status: current
---

# POST /api/products

## Purpose

Creates a new product entry within a specific event. This endpoint is used to initialize product offerings (like tickets or merchandise) that are tied to an event's lifecycle. It is distinct from the `PUT` endpoint in that it enforces a fresh uniqueness check on the `slug` and `event_id` combination to prevent collisions during initial creation.

## Invariants

- **HTTP Method is POST** with a `201 Created` status code on success.
- **Requires `events.edit` permission** via the `require_permission` dependency.
- **Enforces organizational scope** via `_require_event_org_scope` to ensure the product is being created for an event owned by the user's organization.
- **Slug uniqueness is scoped to the event.** A slug only needs to be unique within the same `event_id`, not globally across the entire database.
- **Returns the full `ProductRead` object**, including the newly generated ID and timestamped fields.

## Gotchas

- **Cross-org scope enforcement:** Per commit `058aa8c`, this endpoint relies on `_require_event_org_scope` to prevent a user from injecting a product into an event belonging to a different organization. If the `event_id` in the payload does not match the user's authorized scope, the creation will fail.
- **Slug collisions on update/reassignment:** While this is the POST endpoint, the logic for checking existing slugs is tightly coupled with the `event_id`. If a user attempts to create a product with a slug that already exists in that specific event, the API returns a `400` error.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission via `require_permission`.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Creating a product is a prerequisite for the registration and payment flows managed in the event lifecycle.

## External consumers

- `concorda-web` via `adminProductsApi.create` in `api.ts`.
