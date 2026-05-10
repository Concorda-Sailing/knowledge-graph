---
node_id: GET::/api/auth/validate-reset-token
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 39340e4b01b45bf3a463cb5f721a85ed73cb9117a82c9c42455ea05150683f95
status: current
---

# GET /api/auth/validate-reset-token

## Purpose

Validates a password reset token before the user is presented with the password change form. It ensures the token is not only cryptographically valid but also currently active, unused, and associated with an existing user. This prevents the UI from entering a broken state where a user attempts to reset a password with an expired or invalid link.

## Invariants

- **HTTP Method**: `GET`
- **Query Parameter**: Requires a `token` string.
- **Return Shape**: Returns `{"valid": true, "email": string}` on success.
- **Error State**: Returns `400 Bad Request` if the token is missing, invalid, already used, expired, or if the associated user no longer exists.
- **Token Hashing**: The input `token` is passed through `_hash_token` before database lookup.

## Gotchas

- **Test Environment Echoing**: In test environments, the `reset_token` is echoed back in the `/forgot-password` response (per commit `3582125`) to allow E2E flows to bypass the actual email delivery step.
- **Case Sensitivity**: Per commit `9a5db8f`, ensure any logic involving the user's email (returned by this endpoint) treats the email case-insensitively to match the updated reset/login behavior.

## Cross-cutting concerns

- **Auth**: None (this is a pre-authentication check).
- **Rate limit**: None explicitly defined for this endpoint, but subject to general auth endpoint protections.
- **Side effects**: Success triggers the display of the password reset form in the web client.

## External consumers

- `concorda-web::src/lib/api.ts::authApi.validateResetToken`
