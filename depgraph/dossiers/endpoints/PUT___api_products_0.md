---
node_id: PUT::/api/products/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b89a655606a2e7d72dc11743ee23c18d3e8913bf24fe1918d57c7ebc934754c1
status: llm_drafted
---

# PUT /api/products/{product_id}

## Purpose

Updates an existing product's attributes (such as name, slug, or event association) via a partial update. It is distinct from the creation endpoint in that it performs a strict cross-org scope check on both the current and the destination `event_id` to prevent unauthorized product reassignments.

## Invariants

- **HTTP Method is `PUT`** and requires a `product_id` in the path.
- **Requires `events.edit` permission** via the `require_permission` dependency.
- **Input is `ProductUpdate`**; only fields provided in the payload are updated (via `exclude_unset=True`).
- **Must pass `_require_event_org_scope`** for both the existing `product.event_id` and the new `event_id` if it is being changed.
- **Returns `ProductRead`** shape upon successful update.

## Gotchas

- **Strict cross-org enforcement** — Per commit `058aa8c`, this endpoint enforces tier-C security. If a user attempts to change a product's `event_id` to an event in a different organization, the `_require_event_org_scope` check will trigger a 403/401 failure to prevent "sneaking" products into other clubs.
- **Slug/Event collision** — If a `slug` or `event_id` is updated, the system checks for an existing product with that specific combination. If a collision is found, it raises a 400 error.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission and passes `_require_event_org_scope` check.
- **Audit**: N/A.
- **Side effects**: Updates the `modified` timestamp on the product record.

## External consumers

- `concorda-web::src/lib/api.ts::adminProductsApi.update`

## Open questions

- Should the `slug` validation be more granular to allow for global uniqueness versus event-specific uniqueness? Currently, it is scoped to the `event_id`.
