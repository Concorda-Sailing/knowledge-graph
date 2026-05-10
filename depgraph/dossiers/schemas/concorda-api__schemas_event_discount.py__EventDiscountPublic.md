---
node_id: concorda-api::schemas/event_discount.py::EventDiscountPublic
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6a114210649026feca38b4388c762af8fec7e68ba1bdf5a38ab5601843c3b1d4
status: llm_drafted
---

# EventDiscountPublic

## Purpose

The public-facing representation of an event discount. It strips sensitive internal data (like actual promo codes or internal IDs) to provide a safe view for the frontend. Use this schema when returning discount details via the public API to ensure users can see if a discount is available (via `has_code`) without exposing the actual string required to redeem it.

## Invariants

- **`discount_type`** must be either `"code"` or `"membership"`.
- **`amount_type`** must be either `"flat"` or `"percent"`.
- **`has_code`** is a boolean derived from the presence of a `code` field on the underlying ORM object.
- **`ticket_ids`** is always a list of strings, even if the source data is a JSON string or a related object collection.
- **`from_attributes = True`** is required to allow the `extract_fields` validator to pull data from the ORM model.

## Gotchas

- **`extract_fields` performs manual attribute mapping.** The validator relies on `getattr(data, "code", None)` to set `has_code`. If the underlying model field name changes, this will silently fail to set `has_code` to `True` even if a code exists.
- **JSON deserialization of `ticket_ids`.** If the source `tickets` attribute is not a list of objects but a raw string, the `extract_fields` method performs a `json.loads(raw)` call. If the database contains malformed JSON in the `ticket_ids` field, this schema instantiation will throw a `ValueError`.

## Cross-cutting concerns

- **Auth**: None (this is a public-facing schema).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `GET /api/events/slug/{slug}/discounts` to populate the discount list in the event registration flow.

## External consumers

- Web frontend (registration/checkout flows).
