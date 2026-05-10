---
node_id: concorda-api::models/event_discount.py::EventDiscount
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b9d5262c5a6c4be63970e9b2eeeb3f0f0c6c9d8956c42b3c1b1c93d2ba8ff0a5
status: llm_drafted
---

# EventDiscount

## Purpose

Backend SQLAlchemy model for ticket discounts on event Products. Each row hangs off an `event_id` (no FK constraint — it's a string id field with an index) and applies to either the whole order or a scoped subset of tickets via the `event_discount_tickets` M2M. Two orthogonal axes: `discount_type` ("code" — user types `code`; "membership" — user holds a qualifying `PersonProduct`) and `amount_type` ("flat" dollars or "percent"). `max_uses`/`uses` provides a usage cap; `is_active` is a soft-disable. The admin CRUD lives in `routers/event_discounts.py`; the actual application/selection happens in `POST /api/payments/create-intent`, which picks the single best-savings discount per checkout. Future Claude touching this model should remember: the matcher is in the payments router, not the model.

## Invariants

- `discount_type` is one of `"code"` or `"membership"`; `amount_type` is one of `"flat"` or `"percent"` (free-form `String(20)` columns — no DB enum, no SQLAlchemy validator, so writers must enforce).
- `ticket_ids` JSON column is **deprecated**; the `tickets` M2M via `event_discount_tickets` is the source of truth. New writes go through the junction table (see `routers/event_discounts.py` create/update paths). The column is still read in places but should not be written to.
- `tickets` is empty ⇒ discount applies to the whole order subtotal; non-empty ⇒ scoped to listed Products only. `payments.py` keys off this distinction directly.
- `uses` is incremented atomically with a re-check of `max_uses` at the DB level (`UPDATE ... WHERE uses < max_uses`) — single-row update inside the create-intent transaction. Don't bump it from elsewhere.
- `BaseModel.__init__` is wrapped to hard-code `type="EventDiscount"`; callers must not pass `type=`.
- Mutating routes go through `_require_event_org_scope`: if the event has any organizing authority, the caller must `can_administer_orgs` one of them. `events.edit` permission alone is not sufficient for OA-owned events.

## Gotchas

- "Best discount wins" — the payments router iterates all active discounts on the event, computes savings, and picks the single largest. Discounts do **not** stack, even across membership + code. If a user types a code worth less than their auto-applied membership discount, the membership wins and the code goes uncredited (and `uses` is not incremented on the unused code).
- Code matching is case-insensitive and whitespace-stripped (`.strip().lower()` on both sides). Codes that differ only in case are effectively duplicates; the UI does not warn.
- `membership_id == "any"` (or NULL) is a sentinel meaning "any non-guest Membership"; specific IDs are matched against `PersonProduct.product_id`. The "guest" exclusion is a `LIKE '%guest%'` on `TemporalProduct.name` — renaming a membership to include the word "guest" silently disqualifies it.
- `max_uses` race condition is mitigated only by the atomic UPDATE-with-WHERE in payments.py. Anything else that decrements/increments `uses` (e.g. a future refund flow) needs the same guard.
- Discounts on events with no organizing authority bypass the org-scope check entirely — only the `events.edit` permission gate applies. Legacy social events fall through this way by design.
- The public `GET /api/events/slug/{slug}/discounts` endpoint serializes via `EventDiscountPublic`, which is responsible for hiding `code` values. The internal `EventDiscountRead` exposes them. Don't cross the wires.

## Cross-cutting concerns

- **Payments**: only the create-intent path reads `EventDiscount`. Stripe webhook completion does not re-validate the discount; the `uses` increment happens at intent creation, not at successful charge — a payment that ultimately fails has already burned a use.
- **Permissions**: `events.edit` + org-administrator scoping for mutations; no auth required to read the public list (codes redacted) but the full admin list requires `events.edit`.
- **No NotificationLog/audit entries** for discount application. The applied discount name lands in the `Transaction.notes` string for fully-discounted (charge=$0) orders; partial discounts rely on Stripe metadata.
- **No FK from `event_id` to `events.id`** — orphaned discounts after event deletion are possible. Junction-table FKs to `products` and `event_discounts` do cascade.

## External consumers

None known. Discounts are an internal API surface; no webhooks, no scheduled jobs, no Expo app integration. Stripe sees only the final `charge_amount` after the discount is applied server-side.

## Open questions

- Should discount application move out of `payments.py` into a `services/event_discounts.py` selector so the "best discount wins" logic is testable in isolation and reusable for a future cart-preview endpoint?
- Refund flow is unspecified — does a refunded transaction decrement `uses`? Today it doesn't, which means refunds permanently consume a `max_uses` slot.
- Should `discount_type`/`amount_type` become proper enums (DB CHECK or SQLAlchemy `Enum`) given the free-form `String(20)` is enforced only by Pydantic at the edge?
