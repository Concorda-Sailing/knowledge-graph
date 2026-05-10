---
node_id: concorda-web::src/lib/api.ts::authApi.resetPassword
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f6441e3f84fd63d144439c26a9e189fea4c1806f05770ff0f009683d11c05b2c
status: current
---

# authApi.resetPassword

## Purpose

The `resetPassword` method facilitates the final step of the password recovery flow by submitting a new password alongside a valid reset token. It is distinct from `forgotPassword`, which initiates the process by sending an email, and `validateResetToken`, which verifies the token's validity before the user attempts to change the password.

## Invariants

- **HTTP Method is `POST`** — The request must be a POST to `/api/auth/reset-password`.
- **Payload structure** — Requires a JSON body containing both `token` (string) and `password` (string).
- **Returns a success message** — On successful reset, the API returns an object with a `{ message: string }` shape.

## Gotchas

- **Token lifecycle dependency** — This method relies on a token previously generated and validated via the `forgotPassword` and `validateResetToken` flow. If the token has expired or is invalid, the API will reject the request.

## Cross-cutting concerns

- **Auth**: Uses `fetchApi` (unauthenticated/public endpoint) to allow users who are not currently logged in to reset their credentials.
- **Side effects**: A successful call results in a password change that affects the user's ability to authenticate via `me()` and subsequent `fetchApiAuthenticated` calls.

## External consumers

- `concorda-web::src/app/reset-password/page.tsx::ResetPasswordContent`
