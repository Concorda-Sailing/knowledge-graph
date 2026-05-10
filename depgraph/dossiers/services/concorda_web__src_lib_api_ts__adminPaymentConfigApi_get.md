---
node_id: concorda-web::src/lib/api.ts::adminPaymentConfigApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 866e80017f789029521ec881ecb5e0e624a8da733c2f7d4d306a2469462f0d62
status: current
---

# adminPaymentConfigApi.get

## Purpose

Fetches the current Stripe configuration for the organization. It returns the `PaymentConfigData` object containing the Stripe mode and the necessary public and secret keys. This is used by the admin dashboard to display and manage payment settings.

## Invariants

- **Method is GET** — Performs a read-only fetch of the configuration.
- **Requires authentication** — Uses `fetchApiAuthenticated` to ensure only authorized admins can access sensitive keys.
- **Returns `PaymentConfigData`** — The shape must include `mode`, `stripe_publishable_key`, `stripe_secret_key`, and `stripe_webhook_secret`.

## Gotchas

- **Sensitive Data Exposure** — Because this returns the `stripe_secret_key`, it must never be called from a client-side component that is not strictly protected by admin-only routing.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: The `update` sibling (not this specific node, but part of the same object) is used to modify the keys that drive the payment flow.

## External consumers

- `AdminPaymentPage` in `src/app/members/admin/payment/page.tsx`.
