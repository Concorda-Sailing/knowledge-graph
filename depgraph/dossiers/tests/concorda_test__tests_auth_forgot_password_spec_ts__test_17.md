---
node_id: concorda-test::tests/auth/forgot-password.spec.ts::test@17
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8aa6f3228ffe5ba5fcdd20dcfbd5977aefd55ae35fc09d9c77441d8fab33457a
status: current
---

# submitting valid email shows success message

## Purpose

Verifies the "Forgot Password" flow by ensuring the UI correctly handles email submission. It specifically validates that the success message is visible to the user after a request is sent. This test is distinct from the `login.spec.ts` flows because it focuses on the unauthenticated recovery path rather than session establishment.

## Invariants

- **Success message visibility is required.** The test expects `forgotPage.successMessage` to be visible with a 5,000ms timeout.
- **Information leak prevention.** The test asserts that the UI behavior (showing a success message) is identical whether the email exists in the system or not.

## Gotchas

- **Initial scaffolding.** Per commit `fd0c570`, this is part of the initial E2E suite scaffolding; ensure any changes to the `ForgotPasswordPage` POM (Page Object Model) are reflected here to avoid brittle timeouts.

## Cross-cutting concerns

- **Auth**: Unauthenticated flow; relies on the existence of the `/api/auth/forgot-password` endpoint (or equivalent) to trigger the success state.
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
