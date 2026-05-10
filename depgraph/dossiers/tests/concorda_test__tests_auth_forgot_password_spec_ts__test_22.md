---
node_id: concorda-test::tests/auth/forgot-password.spec.ts::test@22
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 17261c71d0ec3ec79d69a8322a4644c110b12e5f3e81e8d7ee04f5c1d02a9053
status: current
---

# submitting non-existent email still shows success (no information leak)

## Purpose

Verifies that the "Forgot Password" flow does not leak user existence information. It ensures that submitting an email address—whether it exists in the system or not—results in the same success message UI state. This prevents attackers from enumerating registered users via the frontend.

## Invariants

- **Success message visibility.** The test asserts that `forgotPage.successMessage` becomes visible within a 5,000ms timeout.
- **Uniform response.** The UI must show the same success message for both `alice@test.concorda` and `nonexistent@test.concorda`.

## Gotchas

- **Information Leakage Prevention.** Per the test name, the core intent is to ensure the API/Frontend does not differentiate between a valid and invalid email in its response-driven UI.

## Cross-cutting concerns

- **Auth**: Indirectly tests the security posture of the authentication boundary.
- **Side effects**: None.

## External consumers

None known.
