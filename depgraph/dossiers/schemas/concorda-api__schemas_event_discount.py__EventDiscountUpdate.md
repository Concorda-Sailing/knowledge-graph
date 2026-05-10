---
node_id: concorda-api::schemas/event_discount.py::EventDiscountUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d334f5daf3d95b5b10b46b1df40d4a0be75672048eec4157acda5ffca52e386e
status: llm_drafted
---

# EventDiscountUpdate

## Purpose

The schema for updating event-specific discount configurations. It provides a partial model for modifying existing discounts, allowing for the adjustment of types (flat vs. percentage), amounts, and membership/ticket associations. It is distinct from `EventDiscountRead` (which is for full retrieval) and `EventDiscountPublic` (which is for client-side display without sensitive data).

## Invariants

- **`ticket_ids` is a list of strings.** The `parse_ticket_ids` validator ensures that if a JSON string is passed, it is deserialized into a list before validation.
- **All fields are `Optional`.** This allows for partial updates (PATCH-style behavior) where only the changed fields are sent in the request body.
- **`amount` uses `Decimal`.** To prevent floating-point errors in financial calculations, the amount must be a `Decimal` type.

## Gotchas

- **`ticket_ids` deserialization logic.** The `parse_ticket_ids` method handles both raw lists and JSON strings to accommodate different client-side serialization behaviors.
- **`extract_ticket_ids` dependency.** While this specific class is for updates, the sibling `EventDiscountRead` uses a complex `model_validator` to bridge the gap between the ORM's `tickets` relationship and the flat `ticket_ids` list.

## Cross-cutting concerns

- **Auth**: None (handled at the router level in `routers/event_discounts.py`).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Updates to this schema via the `PUT` endpoint will affect the visibility of discounts in the event registration flow.

## External consumers

- `PUT::/api/events/{0}/discounts/{1}` (via `routers/event_discounts.py`).
