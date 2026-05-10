---
node_id: concorda-test::lib/api-client.ts::ApiClient.forgotPassword
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 19ee53cd7b24fca18d074b567ee8ab313a17d8f0dbf070211674267181903ed3
status: current
---

# ApiClient.forgotPassword

## Purpose

The helper for initiating the password reset flow in E2E tests. It posts to `/api/auth/forgot-password` to trigger the backend logic. Unlike `verifyEmail` or `resetPassword`, which require a token, this method is the entry point for testing account recovery scenarios.

## Invariants

- **Method is `POST`** to `/api/auth/forgot-password`.
- **Input is a single string** (`email`).
- **Returns an object with an optional `reset_token`**.
- **The test API is designed to echo the `reset_token`** back in the response so E2E flows can proceed directly to the reset step without needing to intercept actual emails.

## Gotchas

- **E2E flows rely on the echoed token.** Because the test API returns the `reset_token` in the response body, tests like `forgot-password-flow.spec.ts` can "hop straight to /reset-password" by capturing this value, rather than waiting for a real email to arrive in a mailbox.
- **Requires a valid user existence check.** If the email does not exist in the seeded database, the behavior depends on the API's security posture (whether it returns a 200 or 404).

## Cross-cutting concerns

- **Auth**: None (this is a public/unauthenticated endpoint).
- **Side effects**: Triggers the email-sending logic in the test environment (e.g., via `mail-capture.spec.ts`).

## External consumers

- `concorda-test::tests/auth/forgot-password-flow.spec.ts`
- `concorda-test::tests/infra/mail-capture.spec.ts`
