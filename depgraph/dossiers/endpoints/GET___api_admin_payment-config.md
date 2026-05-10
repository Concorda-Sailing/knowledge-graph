---
node_id: GET::/api/admin/payment-config
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2141c04db8a0ca62afbf75f81245b810b06a2cd1ea9accc8d79368b693d6f49e
status: llm_drafted
---

# GET /api/admin/payment-config

## Purpose

Retrieves the current Stripe configuration for the organization. This is a read-only view of the payment processor settings, used by the admin dashboard to display connection status and keys. It is distinct from the `PUT` method in the same file, which handles the actual updates to these credentials.

## Invariants

- **Method is `GET`** and returns a `PaymentConfigResponse`.
- **Auth is required** via `require_auth`.
- **Role-based access** is strictly enforced via `_require_system_admin`.
- **Secrets are masked** in the response via `_mask_secret` for `stripe_secret_key` and `stripe_webhook_secret`.
- **Fallback behavior**: If no `PaymentConfig` record exists in the DB, returns a response with `mode="disabled"` and empty strings for all keys.

## Gotchas

- **Secret masking is mandatory for UI display.** The response shape uses `_mask_secret` to ensure raw keys are not leaked to the client-side unless the `PUT` method is used to overwrite them.
- **Avoid manual string manipulation of secrets.** The `PUT` method contains logic to skip updates if a value starts with `"..."` (per `update_data.items()` check) to prevent overwriting valid secrets with masked placeholders.

## Cross-cutting concerns

- **Auth**: Requires `current_user` with system admin privileges via `_require_system_admin`.
- **Side effects**: Changes to this config (via the sibling `PUT` method) affect the ability of the system to process payments and validate Stripe webhooks.

## External consumers

- `concorda-web::src/lib/api.ts::adminPaymentConfigApi.get`
