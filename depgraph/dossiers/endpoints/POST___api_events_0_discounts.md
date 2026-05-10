---
node_id: POST::/api/events/{0}/discounts
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d04d686186f9e8d2a77d8ee193c8377e6e989e60ae2f5477af22b96a1e3665fe
status: llm_drafted
---

# POST /api/events/{event_id}/discounts

## Purpose

Creates a new discount associated with a specific event. This endpoint manages the creation of the `EventDiscount` record and handles the population of the junction table for associated `ticket_ids`. It is distinct from the `PUT` method in that it handles the initial insertion of the relationship between the discount and the products (tickets) via a dedicated junction table.

## Invariants

- **Requires `events.edit` permission** via the `require_permission` guard.
- **Must pass an existing `event_id`**; if the event does not exist, returns a 404.
- **Enforces organizational scope** via `_require_event_org_scope` to ensure the user is editing an event belonging to their organization.
- **Validates `ticket_ids` against the event**; all provided product IDs must belong to the specified `event_id` or the request fails with a 400.
- **Returns an `EventDiscountRead` object** containing the newly created discount details.

## Gotchas

- **Cross-org scope enforcement** — Per commit `058aa8c`, this endpoint relies on `_require_event_org_scope` to prevent users from injecting discounts into events belonging to other organizations. Failure to call this check or a regression in the check will violate the tier-C security model.
- **Ticket-Event mismatch** — If a `ticket_id` is provided that belongs to a different event, the request fails. This is a hard validation step in lines 71-78 to prevent cross-event product association.

## Cross-cutting concerns

- **Auth**: Requires `current_user` with `events.edit` permission and valid organization scope.
- **Audit**: N/A
- **Rate limit**: None
- **Side effects**: N/A

## External consumers

- `concorda-web::src/lib/api.ts` (via `adminEventDiscountsApi.create`)
