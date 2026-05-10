---
node_id: GET::/api/auth/validate-setup-token
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 18dd477ea16abe914e55758b37b3569b207f5798a5752d156505f55abe8f13f4
status: llm_drafted
---

# GET /api/auth/validate-setup-token

## Purpose

Validates a setup token to ensure a user can proceed to the password creation stage. It checks if a token exists, is not yet used, and has not expired. This is a read-only check used to bridge the gap between receiving an invitation/setup email and the actual account creation via `POST /api/setup-account`.

## Invariants

- **HTTP Method**: `GET`.
- **Query Parameter**: Requires a `token` string.
- **Token Hashing**: The input `token` is passed through `_hash_token(token)` before database lookup.
- **Return Shape**: On success, returns `{ "valid": true, "email": string, "first_name": string }`.
- **Failure Modes**: Returns `400 Bad Request` for invalid, used, or expired tokens, or if the associated user is missing.

## Gotchas

- **Token Hashing**: The client must send the raw token, but the database lookup relies on the hashed version via `_hash_token`. If the hashing logic changes, this endpoint will return "Invalid setup token" even for valid raw tokens.
- **Expiration Logic**: Uses `datetime.utcnow()` for comparison. If the server clock and the token generation time are out of sync, valid tokens may be rejected prematurely.
- **Security Context**: This is a pre-authentication endpoint. It does not require a bearer token, but it is a sensitive entry point for account creation.

## Cross-cutting concerns

- **Auth**: None (pre-auth).
- **Rate limit**: Subject to general auth endpoint rate limiting (see `ec53704` regarding rate limits on auth endpoints).
- **Side effects**: This is a read-only validation; the actual state change (marking the token as used) occurs in the sibling `POST /api/setup-account` endpoint.

## External consumers

- `concorda-web` (via `authApi.validateSetupToken`).
