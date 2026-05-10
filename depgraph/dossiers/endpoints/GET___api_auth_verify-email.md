---
node_id: GET::/api/auth/verify-email
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d99060b70ca3fb3e71cadafbbba18b13759650f0afd3ac7b8c9482956514a198
status: current
---

# GET /api/auth/verify-email

## Purpose

The endpoint for verifying a user's email address via a unique token. It transitions a user from a pending/unverified state to a verified state by validating a token against the `AccountSetupToken` table. This is distinct from `validate_setup_token`, which only checks if a token is valid for display purposes; this endpoint actually performs the state mutation to set `user.email_verified = True`.

## Invariants

- **Method/Path**: `GET /api/auth/verify-email`
- **Input**: Requires a `token` string passed as a query parameter.
- **Token Hashing**: The input token is passed through `_hash_token(token)` before database lookup.
- **State Mutation**: On success, sets `setup_token.used = True` and `user.email_verified = True`.
- **Return Shape**: Returns `{"message": "Email verified successfully"}` on success, or an error detail string on failure.

## Gotchas

- **Environment-specific behavior**: In `CONCORDA_ENV=test`, the verification token is echoed back during registration (per commit `c59841d`) to facilitate automated testing.
- **Expiration handling**: The function uses `datetime.utcnow()` to check against `setup_token.expires_at`. If the token is expired, it returns a 400 error rather than silently failing or returning a success message.
- **Idempotency vs. Error**: If a token has already been used, the function returns a 200 OK with `{"message": "Email already verified"}` instead of raising an exception, preventing user friction if a link is clicked twice.

## Cross-cutting concerns

- **Auth**: No bearer token required; relies on the existence of a valid `AccountSetupToken`.
- **Rate limit**: Subject to auth endpoint rate limiting (see `ec53704`).
- **Side effects**: Triggers the transition of a `Person` record to a verified state, which is a prerequisite for full account access.

## External consumers

- `concorda-web` (VerifyEmailContent page)
- `concorda-test` (ApiClient.verifyEmail)
