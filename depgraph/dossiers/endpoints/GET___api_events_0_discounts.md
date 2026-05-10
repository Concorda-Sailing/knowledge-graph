---
node_id: GET::/api/events/{0}/discounts
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 253b1d4984137ef1973afd05f1d8b67712e3f73f65762b1a89b73823b35df850
status: llm_drafted
---

# GET /api/events/{event_id}/discounts

## Purpose

Retrieves a list of all discounts associated with a specific event. This is a read-only endpoint used to populate the discount management UI for event administrators. It is distinct from the `POST` and `PUT` methods in the same router which handle the creation and modification of discount records.

## Invariants

- **HTTP Method is GET.**
- **Requires `events.edit` permission.** Access is guarded by the `require_permission("events.edit")` dependency.
- **Returns a list of `EventDiscountRead` objects.** The response is a JSON array of discount objects.
- **Ordering is chronological.** Results are ordered by `EventDiscount.created` ascending.

## Gotchas

- **Strict Org-Scope Enforcement.** Per commit `058aa8c`, this endpoint is subject to tier-C cross-org scope enforcement. Users must have administrative access to the organization owning the event to successfully retrieve these records; otherwise, the request will fail or return empty based on the `get_owning_org_ids_for_event` check.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission via `require_permission`.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

- `concorda-web::src/lib/api.ts::adminEventDiscountsApi.list`
