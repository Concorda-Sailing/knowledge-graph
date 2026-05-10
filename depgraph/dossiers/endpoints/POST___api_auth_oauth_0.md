---
node_id: POST::/api/auth/oauth/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 632debdbf1a7c74555ac3bc5a64ca8aa06ac9c6c5615c7c11166029d48822352
status: llm_drafted
---

# POST /api/auth/oauth/{provider}

## Purpose

Provides a placeholder endpoint for third-party OAuth authentication (e.g., Google, Apple). It is intended to handle the exchange of provider-issued tokens for internal session credentials. Currently, this endpoint is a stub that returns a `501 Not Implemented` error to prevent the security vulnerability of accepting unverified client-side identities.

## Invariants

- **Returns `501 Not Implemented`** — The endpoint must always raise an `HTTPException` with status `501` until the server-side verification logic is implemented.
- **Requires a `provider` path parameter** — The string passed in the URL determines the intended OAuth flow (e.g., `google`, `apple`).
- **Must implement server-side verification** — A successful implementation must verify the ID token against the provider's public keys/endpoints rather than trusting the client's payload.

## Gotchas

- **Security Vulnerability (Auth Bypass)** — Per the docstring, the previous implementation accepted raw `oauth_id` or `email` from the client without verification, which allowed users to impersonate others.
- **Verification Requirements** — To move past the 501 error, Google requires `google.auth.transport.requests` and Apple requires verification against Apple's public keys.

## Cross-cutting concerns

- **Auth**: Currently a hard failure; intended to be the primary entry point for OAuth-based identity establishment.
- **Rate limit**: None currently implemented for this specific path, but `ec53704` indicates a general tightening of rate limits on auth endpoints.

## External consumers

None known.

## Open questions

- When should we implement the server-side token verification for Google and Apple? (The docstring explicitly lists the required libraries/methods for both, but no implementation timeline is provided).
