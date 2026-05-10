---
node_id: concorda-api::schemas/event_discount.py::EventDiscountCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ef996d3c52eba9b6c7ace706e18f655c229a9e5855fd7b2924f0051f110a855e
status: llm_drafted
---

# EventDiscountCreate

## Purpose

Defines the input schema for creating a new event discount. It handles both promotional codes and membership-based discounts, supporting both flat amounts and percentages. Use this schema for `POST /api/events/{event_id}/discounts` to ensure valid data structures for discount creation.

## Invariants

- **`discount_type`** must be either `"code"` or `"membership"`.
- **`amount_type`** must be either `"flat"` or `"percent"`.
- **`ticket_ids`** is a list of strings; the `parse_ticket_ids` validator ensures that if a JSON string is passed, it is decoded into a list before validation.
- **`amount`** is a `Decimal` to ensure precision for financial calculations.
- **`is_active`** defaults to `True` if not explicitly provided.

## Gotchas

- **JSON string coercion:** The `parse_ticket_ids` validator handles cases where `ticket_ids` is sent as a raw JSON string rather than a list, a pattern seen in the `EventDiscountUpdate` and `EventDiscountRead` logic to maintain compatibility with legacy or raw input formats.
- **M2M vs JSON column:** Per the `extract_ticket_ids` logic in `EventDiscountRead`, the system is transitioning or dual-handling `ticket_ids`. While `EventDiscountCreate` expects a list, the underlying storage may involve a many-to-many relationship or a legacy JSON column.

## Cross-cutting concerns

- **Auth**: Dependent on the event management permissions (implied by the `POST /api/events/{0}/discounts` route).
- **Side effects**: Creating a discount via this schema affects the pricing logic for event registration and the validation of promotional code application during checkout.

## External consumers

- `POST /api/events/{0}/discounts` (via `routers/event_discounts.py:45`)
