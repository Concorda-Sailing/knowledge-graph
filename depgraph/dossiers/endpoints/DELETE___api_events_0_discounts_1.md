---
node_id: DELETE::/api/events/{0}/discounts/{1}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9b7ce6004499ecbece4397593f2ec81b1e1995420bb269b3ec6444d719fd2952
status: current
---

# DELETE /api/events/{event_id}/discounts/{discount_id}

## Purpose

Deletes a specific discount associated with an event. This endpoint is used by administrators to remove promotional pricing structures once they are no longer valid or were created in error. It is distinct from general merchandise deletion as it specifically targets the link between an event and a discount.

## Invariants

- **HTTP Method is DELETE.**
- **Returns status code 204 (No Content)** on successful deletion.
- **Requires `event_id` and `discount_id`** in the URL path.
- **Requires `events.edit` permission** via the `require_permission` dependency.
- **Validates ownership** via `_require_event_org_scope` to ensure the user belongs to the organization hosting the event.

## Gotchas

- **Cross-org scope enforcement:** Per commit `058aa8c`, this endpoint is strictly guarded by `_require_event_org_scope`. An attempt to delete a discount for an event belonging to a different organization will fail, even if the user has valid `events.edit` permissions globally.
- **Strict 404 behavior:** If the `discount_id` does not exist or is not associated with the provided `event_id`, the API returns a 404.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission and organization-level scope via `_require_event_org_scope`.
- **Audit**: N/A.
- **Side effects**: Deleting a discount may affect the pricing/registration flow for any active or pending registrations tied to that discount.

## External consumers

- `concorda-web` (via `adminEventDiscountsApi.delete`).
