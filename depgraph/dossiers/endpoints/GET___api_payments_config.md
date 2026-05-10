---
node_id: GET::/api/payments/config
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1f92457fc427d539c914a6791d05c69156177d9c8e37d3515f037aa57725fd1d
status: current
---

# GET /api/payments/config

## Purpose

Returns the Stripe configuration required for client-side payment initialization. It provides the `publishable_key` and a boolean `enabled` flag to determine if the checkout UI should be rendered. This is a public endpoint used to check if the organization's payment gateway is active before attempting to create a PaymentIntent.

## Invariants

- **Returns a JSON object** with `publishable_key` (string) and `enabled` (boolean).
- **`publishable_key` is an empty string if disabled.** If the `secret_key` is missing or the mode is set to `"disabled"`, the key is suppressed to prevent client-side errors.
- **No authentication required.** This is a public endpoint used during unauthenticated flows (e.g., new user signups).

## Gotchas

- **Unauthenticated access is required for signups.** Per commit `3750138`, this endpoint (and the broader payment flow) must remain accessible without a session to allow new users to complete checkout/signups without being forced to log in first.

## Cross-cutting concerns

- **Auth**: None (Public endpoint).
- **Rate limit**: None.
- **Side effects**: Controls visibility of the Stripe/Payment UI components in the web app.

## External consumers

- `concorda-web` (via `paymentsApi.getConfig`)
