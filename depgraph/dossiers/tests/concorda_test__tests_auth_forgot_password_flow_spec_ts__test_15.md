---
node_id: concorda-test::tests/auth/forgot-password-flow.spec.ts::test@15
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b0f0a7b49b018bf7c25d3a66cdc4d053843bb7e4e2a2a16180f2cbc5b5557832
status: llm_drafted
---

# user can reset password via emailed link and log in with the new one

## Purpose

Validates the end-to-end lifecycle of a password reset: from the initial `/forgot-password` request to the final verification of the new credentials. It ensures that the UI correctly handles the transition from the email-request state to the reset-token-driven password update state. Unlike the standard `login.spec.ts`, this test relies on a dynamically generated user to avoid side effects on existing test data.

## Invariants

- **Uses a dynamic user identity** — Generates a unique email via `pwreset.${stamp}@test.concorda` to prevent collisions with seeded fixtures.
- **Requires a two-step setup** — The user must be registered and verified via `api.verifyEmail(reg.verification_token!)` before the flow can proceed.
- **Relies on API echo for the reset token** — The test expects the `POST /forgot-password` response to contain the `reset_token` to simulate a user clicking a link from an email.
- **Verifies both success and failure** — A successful reset must allow a new `ApiClient` to login with the new password, while the old password must be rejected.

## Gotchas

- **Success message is intentionally vague** — Per the source comment, the UI uses non-specific wording (e.g., "we've sent a password reset link") to avoid leaking user existence; tests must use regex matches like `/we['’]ve sent a password reset link/i` to avoid brittle string failures.
- **Requires explicit wait for the POST response** — The test must use `page.waitForResponse` on the `/auth/reset-password` endpoint to ensure the password update is processed before attempting to navigate or assert success.
- **Recent tightening of UI assertions** — Commit `ec03c0d` tightened the success-heading match; ensure any changes to the reset success UI do not break the regex-based heading check.

## Cross-cutting concerns

- **Auth**: Tests the full lifecycle of `POST /forgot-password` and `POST /auth/reset-password`.
- **Side effects**: Uses `api.register` and `api.verifyEmail`, which creates a temporary user in the test database.

## External consumers

None known.
