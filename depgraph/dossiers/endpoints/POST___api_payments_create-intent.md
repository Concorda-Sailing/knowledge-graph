---
node_id: POST::/api/payments/create-intent
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7799129de4846deb4a174e933206c4f88503941b5c88f5fc39124c4c6b354151
status: llm_drafted
---

# POST /api/payments/create-intent

## Purpose

Initializes a Stripe PaymentIntent for a transaction involving memberships or event tickets. It calculates the total price by aggregating product prices and quantities, validates that all items belong to the specified `event_id`, and ensures the order does not exceed the maximum allowed ticket quantity. This is the primary entry point for starting a checkout flow on the client side.

## Invariants

- **HTTP Method**: `POST`.
- **Auth**: Requires `get_current_user` (authenticated user), though recent changes allow unauthenticated flows for specific signup paths.
- **Input**: Expects a `CreateIntentRequest` containing a list of `items` (product_id and quantity) and an optional `event_id`.
- **Output**: Returns a `CreateIntentResponse` containing the `publishable_key` and an `enabled` boolean.
- **Price Validation**: If `items` are provided, the total must be greater than zero; otherwise, a 400 error is raised.
- **Product Integrity**: All `product_id`s in the request must exist, be `is_active == True`, and (if `event_id` is provided) belong to that specific event.

## Gotchas

- **Auth requirement change**: Per commit `3750138`, this endpoint was modified to allow unauthenticated new-signup checkouts, whereas it previously required full authentication. This is a critical distinction for the "new user" flow vs. "existing user upgrade" flow.
- **Rate limiting**: The endpoint is protected by an IP-based rate limiter (`_intent_rate_limit`). Rapid successive calls from the same IP will trigger a 429 error.
- **Quantity Cap**: The `MAX_TICKET_QUANTITY` constant is enforced. If a user attempts to add too many tickets to a single order, the request will fail with a 400 error.

## Cross-cutting concerns

- **Auth**: Uses `get_current_user` via dependency injection.
- **Rate limit**: Implements an IP-based sliding window using `_intent_rate_limit` and `_INTENT_RATE_LIMIT_MAX`.
- **Side effects**: Successful completion of the resulting Stripe flow (not handled in this endpoint, but triggered by the intent) eventually updates membership status or event registration.

## External consumers

- `concorda-web` (via `paymentsApi.createIntent` in `api.ts`).
