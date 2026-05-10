---
node_id: concorda-web::src/lib/api.ts::authApi.validateResetToken
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8d226e7124b1c267cf5f6f7497aa3f589162fbcfa3e44954613de25052da7605
status: current
---

# authApi.validateResetToken

## Purpose

Verifies the validity of a password reset token before allowing a user to proceed with a password change. It is a read-only check used by the reset-password flow to ensure the provided token is active and associated with a valid email address.

## Invariants

- **HTTP Method is GET** — The token is passed as a URL query parameter (`?token=...`).
- **Returns `{ valid: boolean; email: string }`** — The response shape is strictly typed to provide both the validity status and the associated email address.
- **Uses `encodeURIComponent`** — The token must be URI-encoded before being passed to the template string to ensure special characters do not break the request.

## Gotchas

- **Dependency for Reset Flow** — The `ResetPasswordContent` component in `src/app/reset-password/page.tsx` relies on this call to gate the password reset UI.

## Cross-cutting concerns

- **Auth**: This is a public-facing auth utility; it does not require a bearer token or an active session, as it is used during the unauthenticated "forgot password" lifecycle.
- **Rate limit**: None specified.

## External consumers

None known.
