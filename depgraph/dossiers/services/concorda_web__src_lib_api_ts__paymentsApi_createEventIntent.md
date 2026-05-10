---
node_id: concorda-web::src/lib/api.ts::paymentsApi.createEventIntent
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 34889d1e82052354daba865966fb13b23d2ae5bc850e26a3d2edc2eab15a539e
status: current
---

# paymentsApi.createEventIntent

## Purpose

Creates a payment intent specifically for event-based transactions. Unlike `createIntent`, which is a generic unauthenticated call, `createEventIntent` checks for an existing auth token to decide whether to use `fetchApiAuthenticated` or `fetchApi`. This allows the system to handle both public-facing product checkouts and authenticated event-specific-payment flows (e.g., paying for a regatta entry) through the same endpoint.

## Invariants

- **Method is `POST`** to `/api/payments/create-intent`.
- **Dynamic Auth Selection**: Uses `getAuthToken()` to toggle between `fetchApiAuthenticated` and `fetchApi`.
- **Input Shape**: Accepts an optional `event_id` and an array of `items` containing `product_id` and `quantity`.
- **Return Type**: Returns a `CreatePaymentIntentResponse` object.

## Gotchas

- **Auth-dependency switch**: The function relies on the presence of a token to determine the fetcher. If `getAuthToken()` returns null, it falls back to `fetchApi`, which may lead to unexpected 401s if the backend expects an authenticated session for specific event-based logic.
- **Product shape mismatch**: Per commit `ef87f614`, the system must ensure the `product_id` or `boat_uuid` is passed correctly through the request chain to avoid failures in downstream crew/payment processing.

## Cross-cutting concerns

- **Auth**: Uses `getAuthToken()` to switch between `fetchApiAuthenticated` and `fetchApi`.
- **Side effects**: Directly impacts the checkout flow on the `PublicEventPage` (see `concorda-web::src/app/events/[slug]/page.tsx`).

## External consumers

- `concorda-web::src/app/events/[slug]/page.tsx::PublicEventPage`
