---
node_id: concorda-api::models/transaction.py::Transaction
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 603091be806ee851e7907e06789e7af160cf6f14c0056068d1ee2c20aa0bd860
status: llm_drafted
---

# Transaction

## Purpose

`Transaction` is the financial-ledger row for everything money-shaped in Concorda: Stripe-backed event-ticket purchases, paid membership signups and pro-rated upgrades, and synthetic $0 rows for free tiers and fully-credited pro-rations. It carries who paid (`person_id`, nullable for guest checkout), what was paid for (`product_id` + `product_type` discriminator: `"Product"` for event tickets, `"TemporalProduct"` for memberships), how much (`amount`), where Stripe knows it (`external_reference` = PaymentIntent id, UNIQUE), and the lifecycle state (`status` ∈ {Pending, Completed, Failed, AmountMismatch}). It is the binding handle between Stripe's async webhook world and the synchronous "I'd like to register / upgrade now" requests — every paid downstream commit (`EventRegistration`, `PersonProduct`) requires looking up a Transaction by id, asserting `status="Completed"`, and asserting `person_id` matches the caller. A future Claude editing this should treat it as a security boundary first and a ledger second: the `(transaction_id, person_id)` binding gates all paid redemption and is the surface where the load-bearing security fix lives.

## Invariants

- **`type="Transaction"` is hard-coded in `__init__`** — single-table-style discriminator on `BaseModel.type`; never override.
- **`external_reference` is UNIQUE** and is the Stripe PaymentIntent id (or `NULL` for synthetic $0 rows that never touched Stripe). The webhook handler keys on it as the sole lookup; duplicates would route Stripe events to the wrong row.
- **`person_id` is nullable on purpose** — guest checkout creates `person_id=NULL` Transactions; the registration call later redeems them with the same NULL identity. The pending-auth signup flow (`POST /api/auth/register`) creates a NULL-person Transaction at `/create-intent` time and back-fills `person_id` once the user record exists (`auth.py:735`).
- **`amount` is `Numeric(10,2)`** — not float. Compare Stripe's `payment_intent.amount_received` (integer cents) as `int(transaction.amount * 100)`; the webhook does this explicitly to detect tampered client-side amounts (sets `status="AmountMismatch"`).
- **`status` is a 5-value string enum, app-enforced** — `Pending` (default), `Completed`, `Failed`, `AmountMismatch`, and the unwritten `Refunded`. No DB CHECK constraint; no state-machine guard rails.
- **`expected_quantity` carries the order size** for multi-ticket purchases (default `1` when consumed). `EventRegistration` redemption blocks when `count(confirmed regs for txn) >= expected_quantity`; off-by-one here = double-redemption.
- **Paid redemption MUST bind `Transaction.person_id == caller_id` (or both NULL)** at every consume site. See the candidate `rule::payments::transaction_person_binding`. The NULL-NULL branch is intentional, not a fallback hole.
- **`product_type` is the discriminator that routes redemption** — `"Product"` → mints `EventRegistration`; `"TemporalProduct"` → mints `PersonProduct` entitlement. There is no FK enforcing this convention.
- **`date` defaults to naive `datetime.utcnow`** — this model predates the `UtcDateTime` convention (see `feedback_naive_datetime_convention`). Reads return naive datetimes; renderers must treat as UTC. New datetime columns on this table should use `UtcDateTime`.

## Gotchas

- **The security fix `74962cb` (`fix(security): bind paid registrations`) is the load-bearing event on this surface.** Pre-fix, any logged-in user could pass another user's `transaction_id` to `/register` and consume their payment. The current binding is `Transaction.person_id == current_user.id` (or both NULL for guest). The NULL-NULL branch (`3750138`, guest checkout) is intentional — don't "tighten" it without preserving the guest path.
- **Lazy-promote is real.** When the browser POSTs `/register` before Stripe's webhook arrives, `events.py:1715-1724` re-fetches the PaymentIntent directly from Stripe, flips the Transaction to Completed, and proceeds. This self-heal path means a Transaction can transition `Pending → Completed` from *two* sources (webhook and registration); don't add invariants that assume webhook is the sole writer.
- **`AmountMismatch` is a tamper signal, not a refund.** Stripe collected money but our `Transaction.amount` disagreed with `payment_intent.amount_received`. The row is left mid-state — no refund, no notification, no admin alert. If this ever fires in prod, manual reconciliation is required.
- **No DB FK on `external_reference`-related lookups** and no FK from `EventRegistration.transaction_id` or `PersonProduct` back to this table. Hard-deleting a Transaction silently orphans downstream rows.
- **Synthetic $0 rows split into two flavors with different bypasses.** Free membership signup (`auth.py:738-747`) creates `status="Completed"` *without* `external_reference` and *without* category-side validation. Pro-rated-to-zero upgrades (`payments.py:365-378`) do the same but with `notes="Pro-rated to $0"`. Both bypass the "payment required" gate cleanly — don't add a `external_reference IS NOT NULL` filter to redemption without handling these.
- **`organization_id` exists on the column list but is never written.** None of the five callers populate it. Treat as dead weight / future-org-scoping until someone wires it up.
- **`payment_failed` webhook does not retry or notify** — flips `status="Failed"`, writes the error message to `notes`, returns 200. The user sees only their Stripe-side failure UI; the backend never emails them.

## Cross-cutting concerns

- **Auth boundary.** This is the load-bearing surface for the candidate `rule::payments::transaction_person_binding`. Five consume sites: `register_for_event` (events.py:1704), `membership/upgrade` (profile.py:1364), `payments/webhook` (payments.py:476), `auth/register` (auth.py:735, backfill not consume), `payments/create-intent` (payments.py:396, write only). All paid-redemption paths filter by `person_id == caller_id` (or both NULL).
- **Stripe lifecycle.** Pending → Completed is normally driven by `payment_intent.succeeded` webhook; Pending → Failed by `payment_intent.payment_failed`; Pending → AmountMismatch by amount-comparison in the webhook. The lazy-promote path in `register_for_event` is a parallel writer to Completed.
- **Single-uvicorn-worker constraint** (see `feedback_rate_limiter_single_worker`) applies indirectly — the `/create-intent` endpoint sits behind the in-memory rate limiter; horizontal scaling needs Redis first.
- **Membership atomicity** (candidate `rule::membership::single_membership_personproduct`) consumes Transactions in the delete-then-insert section of `/membership/upgrade`. Inserting I/O between Transaction lookup and `PersonProduct` commit breaks the atomicity guard.
- **No websocket broadcast** on Transaction status changes. Downstream `PERSON_UPDATED` fires on the membership-upgrade success path; the Transaction itself is invisible to clients.
- **No audit log.** Status transitions are not journaled; the only forensic trail is `notes` (free-form string) and Stripe's own dashboard.
- **Refund story is absent.** `status="Refunded"` is unwritten; no refund endpoint exists. Cancelling an `EventRegistration` does not propagate here. Capacity is freed; money is not.

## External consumers

- **Stripe** — the only true external dependency. PaymentIntents are created in `payments.py:create_payment_intent` and matched back via `external_reference`. Webhook endpoint at `POST /api/payments/webhook` is the canonical state-flipper.
- **Concorda web `paymentsApi.getConfig`** — initializes Stripe Elements with the publishable key; no direct Transaction knowledge, but every paid path depends on it.
- **Concorda iOS app** — does not currently invoke Stripe (mobile payments unshipped). The free-signup path on iOS would still mint synthetic $0 Transactions via `/auth/register`.
- **No scheduled jobs, no external webhooks beyond Stripe, no email-from-Transaction triggers.**

## Open questions

- **Refund + chargeback design.** When the first chargeback or admin-refund lands, Product capacity, EventRegistration status, and Transaction status all need a coordinated story. Currently none exist.
- **`organization_id` semantics.** Column is written by nobody. Intended for org-scoped revenue reporting? Drop it or wire it up.
- **DB-level constraints.** Status enum, `external_reference` non-null for non-synthetic rows, and FKs from `EventRegistration.transaction_id` / `PersonProduct` would catch a class of orphan/tamper bugs.
- **Should `date` migrate to `UtcDateTime`?** Currently naive `datetime.utcnow`; pre-2026-05-06 imports may drift. Low priority but worth scheduling.
- **AmountMismatch handling.** Right now it's a silent forensic flag. Should it page, refund, or notify?
