---
node_id: PUT::/api/events/{0}/discounts/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: db6243b2d3c6348e326fa060734bc184a7e069ca1a8a7ea9cae73f2cd3084929
status: current
---

# PUT /api/events/{event_id}/discounts/{discount_id}

## Purpose

Updates the configuration of an existing event discount. This endpoint manages both the core discount attributes and the associated ticket/product mapping. It is distinct from the `DELETE` method in the same router, which removes the discount entirely; this `PUT` method is used for modifying existing discount rules, such as changing the discount amount or updating the set of eligible tickets.

## Invariants

- **HTTP Method is `PUT`** — used for full updates of the `EventDiscount` resource.
- **Requires `events.edit` permission** — enforced via `require_permission("events.edit")`.
- **Mandatory `event_id` and `discount_id`** — both must be provided in the URL path.
- **Returns `EventDiscountRead`** — the response shape is the updated discount object.
- **`ticket_ids` handling is destructive** — providing a new list of `ticket_ids` replaces the existing association in the junction table.

## Gotchas

- **Strict Org Scope Enforcement** — per commit `058aa8c`, this endpoint uses `_require_event_org_scope` to ensure the user has access to the specific organization owning the event. This prevents cross-org discount manipulation.
- **Ticket Validation is strict** — if `ticket_ids` are provided, they must belong to the `event_id` specified in the URL. If a user attempts to attach a ticket from a different event, the API throws a 400 error (see logic in lines 111-121).
- **`exclude_unset=True` behavior** — the `update_data` is derived from `data.model_dump(exclude_unset=True)`. Only fields explicitly sent in the request body will be updated on the `discount` object.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission and passes the `_require_event_org_scope` check.
- **Audit**: N/A.
- **Side effects**: Updates to this endpoint affect the visibility and applicability of discounts on the event's registration/checkout pages.

## External consumers

- `concorda-web` (via `adminEventDiscountsApi.update`)
