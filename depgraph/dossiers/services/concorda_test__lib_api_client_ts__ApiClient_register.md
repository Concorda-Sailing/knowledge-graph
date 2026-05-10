---
node_id: concorda-test::lib/api-client.ts::ApiClient.register
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fcd178f9d5fbb0f0d3524713d7213c41759b6b4046357370116ec922ecc11d7f
status: llm_drafted
---

# ApiClient.register

## Purpose

Provides a public self-service registration method for the test environment. It abstracts the `POST /api/auth/register` endpoint, automatically injecting required default preferences (e.g., `directory_opt_in: true`) and TOS acceptance to ensure the created user is fully initialized for E2E flows. Use this instead of manual API calls when a test requires a fresh, unauthenticated user-creation step.

## Invariants

- **Method**: `POST /api/auth/register`.
- **Return Shape**: Returns an object containing `requires_verification` (boolean), `user_id` (string), and an optional `access_token` and `verification_token`.
- **Automatic Defaults**: Hardcodes `tos_accepted: true` and sets specific `preferences` (directory opt-in/show email/show phone) to bypass the need for manual preference configuration during registration.
- **Date Format**: The `date_of_birth` field (if provided) must follow the `YYYY-MM-DD` ISO format.

## Gotchas

- **TOS/Policy requirement**: Per commit `c70d472`, the registration flow or subsequent user actions may fail if pending policies aren't handled. While `register` sets `tos_accepted: true`, certain flows may still require calling `acceptAllPendingPolicies()` via the `ApiClient` to satisfy the backend's policy engine.
- **Verification Loop**: The test API is designed to echo the `verification_token` back in the response. This is a specific test-environment behavior to allow E2E flows to call `verifyEmail(token)` immediately without needing to simulate a mailbox/email-scraping step.

## Cross-cutting concerns

- **Auth**: Creates a new user identity; the resulting `access_token` can be used to establish a new session via `setToken`.
- **Side effects**: Successful registration creates a new user record in the database, which is a prerequisite for testing flows like `crew-signup-flow.spec.ts`.

## External consumers

- `concorda-test::tests/auth/crew-signup-flow.spec.ts`
- `concorda-test::tests/auth/forgot-password-flow.spec.ts`
