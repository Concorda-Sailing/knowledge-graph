---
node_id: concorda-api::models/event_registration.py::EventRegistration
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5891ab1b4549f8cb8d851a56e58ce395f424a87900003f7b846249e134519f41
status: llm_drafted
---

# EventRegistration

## Purpose

`EventRegistration` is the per-person, per-event commitment record — the row that says "this email/person is registered for this ticket type at this event." It is created either by `POST /events/slug/{slug}/register` (post-payment for paid tickets, immediate for free) or as the receipt of a Stripe checkout flow that minted a `Transaction(product_type="Product")`. It is deliberately **distinct from `EventCrew`**, which is the per-event crew slot for racing (boat-scoped, position-scoped, accept/decline lifecycle); EventRegistration carries no boat, no position, no crew priority — just identity, ticket, status, and an optional bound transaction. When future Claude is touching ticket purchases, attendance lists, sold-out math, registration confirmation pages, or the "Events I'm registered for" view on `/my-schedule`, this is the model.

## Invariants

- **`type="EventRegistration"` is hard-coded in `__init__`.** Single-table-style polymorphism via `BaseModel.type`; never override the discriminator.
- **`product_id` is NOT NULL.** Every registration is for a specific `Product` (ticket SKU). There is no "registered without a ticket" path; even a $0 free-ticket registration carries a Product row.
- **`person_id` IS nullable.** Anonymous/guest registration is a first-class flow — paying without an account is supported and the registration is identified by `email` only. The `email` index exists for this reason.
- **`transaction_id` is nullable but unenforced as FK** (raw `String(36)` column, no `ForeignKey("transactions.id")`). Free tickets (`product.price == 0`) MUST have `transaction_id = NULL`; paid tickets MUST have a non-null transaction whose `Transaction.status == "Completed"` and whose `person_id` matches the caller (or both NULL for guest-checkout). See `events.py:1694-1727`.
- **Default `status = "Confirmed"`.** The model never writes "Pending" — `register_for_event` constructs the row only after payment validates, so by the time it lands the registration is already Confirmed. "Cancelled" is the only other observed value, set by `DELETE /api/profile/event-registrations/{id}` (`profile.py:355`).
- **Sold-out and "already registered" guards filter on `status == "Confirmed"`.** A Cancelled row leaves the seat available and the email free to re-register. Don't change that semantics without auditing all five `status == "Confirmed"` filters.
- **Quantity gate is enforced via `count(EventRegistration where status="Confirmed" and product_id=p.id)`,** not on the `Product` row. There is no decrement counter; this table IS the inventory ledger.
- **`(event_id, product_id, email, status="Confirmed")` is the de-facto uniqueness key,** app-enforced in two places (`events.py:1550-1559` for pre-check, `events.py:1736-1743` for the actual register call). There is no DB UNIQUE; concurrent requests can in principle slip through.

## Gotchas

- **Only one commit ever touched this model: `6405007` (the original event-management feature drop).** Every behavioral change since has been in the routers. Don't expect schema git-blame to tell you the story — read `routers/events.py` and `routers/payments.py`.
- **`74962cb` (`fix(security): bind paid registrations`) was the load-bearing fix on this surface.** Pre-fix, `register_for_event` looked up the supplied transaction by id+status only — any logged-in user could pass another user's `transaction_id` and consume it. The current binding is `Transaction.person_id == current_user.id` (or both NULL for the anonymous-checkout flow). The anonymous-NULL branch is **intentional**, not a fallback hole — guest checkout creates a NULL-person Transaction and the same NULL-person caller redeems it. Don't "tighten" this without understanding the guest path.
- **Pending vs Confirmed is not a state machine on this row** — it's a state machine on the upstream `Transaction`. The Pending half lives on `Transaction.status="Pending"` until Stripe webhook (or the lazy-promote path in `register_for_event`) flips it to Completed. EventRegistration only exists in Confirmed (or, post-cancellation, Cancelled).
- **Multi-ticket transactions create N separate EventRegistration rows from one Transaction.** `Transaction.expected_quantity` carries the order size; `events.py:1729-1734` blocks redemption when `count(confirmed regs for txn) >= expected_quantity or 1`. Off-by-one here = double-redemption. The frontend must call `register_for_event` once per attendee and supply distinct names/emails — there is no bulk endpoint.
- **Sold-out and dup-email checks are TOCTOU-vulnerable.** Concurrent `register_for_event` calls can both pass the count check before either commits. There's no DB UNIQUE on `(event_id, product_id, email, status)` and no `SELECT … FOR UPDATE`. Hasn't bitten in production but isn't theoretical-only at scale.
- **`person_id` is set from `current_user`, but `email` is taken from the request body unconditionally.** A logged-in user can register a friend by typing the friend's email — it'll record `person_id=mine, email=friend's`. The de-dup guard keys on email, not person_id, which is intentional (preserves guest semantics) but means a single user can rack up unlimited registrations for distinct emails on one paid transaction (capped only by `expected_quantity`).
- **Cancellation is soft-delete only.** `DELETE /api/profile/event-registrations/{id}` flips `status="Cancelled"`. There is no Stripe refund, no Transaction status change, no audit log entry, and no email notification. Re-registering after cancel is allowed.
- **`product.name if product else "Unknown"`** scattered through `events.py:1597, 1648` is a defensive shim against `Product` hard-deletes — there's no FK cascade, so a deleted Product leaves orphan registrations. Don't remove the defensive nones until you fix the cascade story.

## Cross-cutting concerns

- **Stripe transaction lifecycle.** EventRegistration creation is the *terminal* step of the payment funnel: Stripe `payment_intent.succeeded` webhook flips `Transaction.status` to Completed; the user's browser then POSTs `/register` with the `transaction_id`; this row is finally inserted. The lazy-promote path in `register_for_event` (`events.py:1715-1724`) self-heals when the user beats the webhook.
- **Event capacity.** `Product.quantity` is the cap, EventRegistration is the counter. Sold-out math runs at three call sites: `/tickets` (display), `/check-registration` (pre-payment optimistic check), `/register` (final guard). All filter `status == "Confirmed"`. If you add a fourth ticket-sales path, replicate the count exactly — there is no shared helper.
- **Product redemption.** Buying a Product mints an EventRegistration (vs. buying a TemporalProduct which mints a `PersonProduct` entitlement). The `(Transaction.product_type == "Product") → EventRegistration` mapping is implicit — there is no FK enforcing it, only the convention in `payments.py` and `events.py`.
- **Refund story is absent.** No refund endpoint exists. `Transaction.status="Refunded"` is unwritten. Cancelling an EventRegistration does **not** propagate to the Transaction or Stripe. Capacity is freed but the money is not. When the first chargeback or admin refund request lands, the gap surfaces simultaneously on Product, Transaction, and EventRegistration — design it once, not three times.
- **Auth.** Public POST `/register` (optional auth) on non-members-only events; admin-only `events.edit` permission for `GET /events/{id}/registrations`; user-scoped self-service via `/profile/event-registrations[/{id}]`. The confirmation endpoint does its own ownership check (email match OR person_id match OR admin) — it intentionally allows logged-out access if you have the registration ID.
- **`/my-schedule` integration.** `events.py:227-238` joins on EventRegistration to surface "events I'm registered for" alongside personal/bookmarked/crew rows. Filters `status == "Confirmed"` and `Event.date >= start-of-today UTC` per the schedule-floor convention. See `rule::schedule::canonical_listing` — registrations are one of the five sources.
- **No websocket broadcast** on registration creation/cancellation. The SPA refetches.
- **No logigraph rules** target this node currently.

## External consumers

- **Stripe** — receives the `transaction_id` indirectly via PaymentIntent metadata. No direct Stripe knowledge of EventRegistration.
- **Concorda iOS app** — reads `/profile/event-registrations` for the user's registered-events list and `/events/slug/{slug}/my-registration` on the public event page.
- **Email** — confirmation/registration emails read from EventRegistration via the routers, not from the model directly.
- **No external webhooks or scheduled jobs** consume this model.

## Open questions

- **Refund + cancellation propagation.** The cancel sets `status="Cancelled"` but does not refund, does not notify, and does not free the seat in any audit-visible way. What's the right end-to-end story?
- **DB-level UNIQUE on `(event_id, product_id, email, status)`?** App-enforced now. Same TOCTOU caveat as Product slug uniqueness.
- **FK on `transaction_id`.** Currently raw `String(36)`. A real `ForeignKey("transactions.id")` would catch the orphan-on-Product-delete class of bugs.
- **De-dup keying on email vs person_id.** The current scheme allows a logged-in user to register multiple friends under their own person_id; is that a feature or a hole?
- **Bulk-register endpoint.** Multi-ticket purchases require N round-trips. Is that the design, or just where we stopped?
