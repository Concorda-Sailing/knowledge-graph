---
node_id: POST::/api/auth/resend-setup-email
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: de323e24d2a6e7a1afac7526a329ff7724b4f9da4e27fe19fcf1acde1bc0505a
status: current
---

# POST /api/auth/resend-setup-email

## Purpose

Triggers the re-sending of an account setup email for a user who has not yet completed their registration. It generates a new `AccountSetupToken`, invalidates any existing unused tokens for that user, and sends the email via `send_account_setup_email`. This is distinct from `forgot_password`, which handles existing accounts; this endpoint is specifically for the pre-registration/onboarding phase.

## Invariants

- **Returns a constant success message** regardless of whether the email exists or a password is already set. This prevents user enumeration/information leakage.
- **Invalidates existing tokens** by setting `used = True` on any existing `AccountSetupToken` for the user before creating the new one.
- **Input is a `ResendSetupEmailRequest`** containing the target email address.
- **Rate limiting is applied by email address** to prevent spamming users with setup links.

## Gotchas

- **Rate limiting is skipped in test environments** via the `_RATE_LIMITS_DISABLED` flag.
- **Email matching is case-insensitive** per commit `9a5db8f`, ensuring that `request.email.strip().lower()` correctly identifies the user even if the input casing differs from the DB record.
- **Security/Information Leakage:** The endpoint is designed to be non-revealing. If a user is not found or already has a `password_hash`, the response is identical to a successful trigger to prevent attackers from probing for valid setup emails.

## Cross-cutting concerns

- **Auth**: None (this is a pre-auth endpoint).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: Uses `_resend_setup_rate_limit` keyed by email; behavior is controlled by `_RATE_LIMITS_DISABLED`.
- **Side effects**: Triggers `send_account_setup_email` which interacts with the external email provider.

## External consumers

- `concorda-web::src/lib/api.ts::authApi.resendSetupEmail`
