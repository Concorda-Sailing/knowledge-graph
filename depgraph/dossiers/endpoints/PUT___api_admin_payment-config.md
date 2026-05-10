---
node_id: PUT::/api/admin/payment-config
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 611d23e045752fbdae685b1622be2acbf968f81891f28bfc17d670732975912e
status: llm_drafted
---

# PUT /api/admin/payment-config

## Purpose

Updates the global payment processor configuration, specifically for Stripe integration. This endpoint allows an administrator to set the `mode` (e.g., test vs. live) and the necessary API keys. It is distinct from the `OrgConfig` endpoints, which handle branding and local settings; this is strictly for the financial/payment gateway layer.

## Invariants

- **Requires `require_auth` and `_require_system_admin`** — Only users with system-level administrative privileges can modify these settings.
- **Returns `PaymentConfigResponse`** — The response includes the current `mode`, `stripe_publishable_key`, and both `stripe_secret_key` and `stripe_webhook_secret`.
- **Masks sensitive data** — The `stripe_secret_key` and `stripe_webhook_secret` are passed through `_mask_secret` in the response to prevent leaking full keys to the client.
- **Prevents accidental overwrites via placeholders** — If a value in `update_data` starts with `"..."`, the update for that specific field is skipped to prevent replacing a valid secret with a masked placeholder string.

## Gotchas

- **Secret field protection** — The logic in `update_payment_config` explicitly checks `if value.startswith("...")` to avoid overwriting existing secrets with the masked strings returned by the API. This is a critical guard to prevent the UI from accidentally "clearing" a secret when it simply re-submits the masked version.
- **Privilege escalation risk** — Per commit `650233f`, there is a strict requirement to ensure that only `_require_system_admin` can access this endpoint to prevent unauthorized users from hijacking the payment flow.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` and `_require_system_admin`.
- **Side effects**: Changes to the `mode` or keys will affect all successful/failed payment processing and webhook validation across the platform.

## External consumers

- `concorda-web::src/lib/api.ts::adminPaymentConfigApi.update` (via `http_call`)
