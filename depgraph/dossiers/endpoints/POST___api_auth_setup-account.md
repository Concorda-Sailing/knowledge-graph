---
node_id: POST::/api/auth/setup-account
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 98ceee88c4de636d18ea8b012070eb22b140cc24d3223e66491e47ea31cb378f
status: llm_drafted
---

# POST /api/auth/setup-account

## Purpose

Completes the onboarding flow by allowing a user to set a password and verify their identity using a single-use setup token. This endpoint transitions a `Person` record from a pending/unverified state to a fully authenticated state. It is distinct from the standard login flow as it requires a valid `AccountSetupToken` and performs the initial `password_hash` generation.

## Invariants

- **Requires a valid `token`** — The token is hashed via `_hash_token` before lookup to prevent timing attacks or plain-text exposure in logs.
- **Returns a bearer token** — On success, returns `{access_token, token_type}` for immediate session establishment.
- **Single-use only** — Once the password is set, `setup_token.used` is set to `True` and the token cannot be reused.
- **Expiration-sensitive** — The request fails if `datetime.utcnow()` is greater than the `setup_token.expires_at` timestamp.
- **Sets `email_verified = True`** — Successful execution automatically marks the user's email as verified.

## Gotchas

- **Case-sensitivity in lookup** — Per commit `9a5db8f`, ensure that any logic involving email lookups (which may precede this call in the UI) treats emails case-insensitively to avoid "User not found" errors during the setup flow.
- **Test environment bypass** — In the test environment, the `_RATE_LIMITS_DISABLED` flag (referenced in `resend_setup_email` but relevant to the auth router's behavior) may allow much higher throughput than production.
- **Password validation failure** — If `validate_password` fails, the endpoint returns a `400 Bad Request` with the specific error string; this is a client-side validation error, not a token error.

## Cross-cutting concerns

- **Auth**: Generates the initial `access_token` via `create_token`.
- **Rate limit**: While this specific endpoint is the destination, it is part of the auth-router logic where `_resend_setup_email` implements a windowed rate limit to prevent spamming setup links.
- **Side effects**: Transitions the `Person` record from a pending state to an active user, enabling access to all authenticated features.

## External consumers

- `concorda-web` (via `authApi.setupAccount`)
