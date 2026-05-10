---
node_id: concorda-web::src/lib/api.ts::paymentsApi.createIntent
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b2ce8890b08ab69055fc21e82fe48b62b204c14b6b6bdd13de5d06d4eed16bfd
status: current
---

# paymentsApi.createIntent

## Purpose

Initiates a payment process by creating a payment intent on the server. It is used to transition from a product selection/registration state to a checkout state. Use `createIntent` for standard product-based flows and `createEventIntent` when the payment is contextually tied to a specific event or requires a more complex payload (like items or discount codes).

## Invariants

- **HTTP Method is `POST`** — always sent to `/api/payments/create-intent`.
- **Input is a `product_slug`** — the primary identifier for the item being purchased.
- **Returns `CreatePaymentIntentResponse`** — the response shape is required by the frontend to initialize the payment provider (e.g., Stripe/Adyen) client-side.
- **`createEventIntent` uses `fetchApiAuthenticated`** — unlike the base `createIntent`, this variant requires a valid auth token to resolve the `token` via `getAuthToken()`.

## Gotchas

- **`createEventIntent` dependency** — if `getAuthToken()` returns null, the fetcher switches to `fetchApi`, which may lead to unexpected 401s if the endpoint expects an authenticated session.
- **Payload mismatch** — `createIntent` only accepts `{ product_slug: string }`, whereas `createEventIntent` accepts an optional `event_id` and `items` array. Passing the wrong object shape to the wrong method will fail at the API level.

## Cross-cutting concerns

- **Auth**: `createIntent` is unauthenticated; `createEventIntent` depends on `getAuthToken()`.
- **Side effects**: Used by `RegisterPageContent` in the `/join/register` flow and the `MembershipUpgrade` component to trigger checkout transitions.

## External consumers

- None known.
