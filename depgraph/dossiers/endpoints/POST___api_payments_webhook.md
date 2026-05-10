---
node_id: POST::/api/payments/webhook
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2fa90658d01596ca80e1f50a1884729f55d60797da2ac756c57bfedfeda20ccb
status: current
---

# POST /api/payments/webhook

## Purpose

The primary endpoint for receiving asynchronous event notifications from Stripe. It validates the incoming request signature and updates the status of internal `Transaction` records based on `payment_intent` events. This is the single source of truth for transitioning a transaction from a pending state to `Completed`, `Failed`, or `AmountMismatch`.

## Invariants

- **Signature Verification is Mandatory.** The endpoint uses `construct_webhook_event` to validate the `stripe-signature` header; failure to validate results in a 400 error.
- **Transaction Lookup via `external_reference`.** The endpoint identifies the internal transaction by matching the `payment_intent.id` against the `Transaction.external_reference` field.
- **Amount Validation.** For `payment_intent.succeeded` events, the code compares the received amount (in cents) against the expected amount (stored as a Decimal in the database) to detect discrepancies.
- **Status Transitions.** Successful payments set status to `Completed`, while failed payments set status to `Failed`.

## Gotchas

- **Unauthenticated Access.** Per commit `3750138`, this endpoint must remain unauthenticated to allow Stripe to post events, but it is specifically designed to handle the logic for both new-signup checkouts and membership upgrades.
- **Amount Mismatch Handling.** If `payment_intent.amount_received` does not match the expected cents, the transaction is marked as `AmountMismatch` rather than `Completed`. This prevents silent failures in pro-rated billing logic.

## Cross-cutting concerns

- **Auth**: None (relies on Stripe signature verification via `construct_webhook_event`).
- **Audit**: Y (updates `Transaction.status` and `Transaction.notes`).
- **Side effects**: Updates the status of the `Transaction` model, which is the upstream source for membership/access status in the user's account.

## External consumers

Stripe (via webhook).
