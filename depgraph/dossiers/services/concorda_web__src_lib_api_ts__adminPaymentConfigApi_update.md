---
node_id: concorda-web::src/lib/api.ts::adminPaymentConfigApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 71d2138194b6e2fc7e4ae0c139b80dfd1a5cb20d41ba04014f0c209abc42300e
status: current
---

# adminPaymentConfigApi.update

## Purpose

Provides a method to update the organization's Stripe configuration, including the publishable and secret keys and the webhook secret. This is a high-privilege administrative action used to manage the payment gateway settings for the organization. It is distinct from the `get` method in that it accepts a `Partial<PaymentConfigData>` to allow for incremental updates to the configuration.

## Invariants

- **HTTP Method is `PUT`** — The endpoint requires a PUT request to update the existing configuration.
- **Uses `fetchApiAuthenticated`** — The request must include a valid administrative bearer token.
- **Input is a `Partial<PaymentConfigData>`** — Only the fields being changed need to be provided in the request body.
- **Returns `PaymentConfigData`** — A successful update returns the full, updated configuration object.

## Gotchas

- **Sensitive Data Handling** — Because this method handles `stripe_secret_key` and `stripe_webhook_secret`, any consumer of this API must ensure these values are handled with extreme care and not logged or exposed in client-side debugging tools.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session via `fetchApiAuthenticated`.
- **Side effects**: Updates to this configuration will affect the behavior of any Stripe-related logic in the backend (e.g., webhook verification and payment processing).

## External consumers

- `AdminPaymentPage` in `concorda-web/src/app/members/admin/payment/page.tsx`.
