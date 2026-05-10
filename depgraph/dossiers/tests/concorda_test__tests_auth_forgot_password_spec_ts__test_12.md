---
node_id: concorda-test::tests/auth/forgot-password.spec.ts::test@12
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a3b765ba9930fe75b683f35759a3e428a61b740c50d42613166dc4d282ad213a
status: llm_drafted
---

# page loads with email input and submit button

## Purpose

Verifies the UI state and behavior of the "Forgot Password" flow. It ensures the email input and submit button are visible and, crucially, validates the security-critical behavior that the UI provides a uniform success message regardless of whether the email exists in the system.

## Invariants

- **Success message visibility** — The `successMessage` must be visible within a 5,000ms timeout to account for potential network latency in the test environment.
- **Information Leak Prevention** — The UI must present the same success message for both valid and non-existent email addresses to prevent user enumeration.

## Gotchas

- **Initial scaffolding only** — Per commit `fd0c570`, this is part of the initial E2E suite scaffolding; it currently only tests basic visibility and the uniform success message, not the actual backend trigger or email delivery.

## Cross-cutting concerns

- **Auth**: Indirectly tests the security boundary of the authentication system by ensuring the UI does not leak user existence via the password reset flow.
- **Side effects**: Verifies the UI-side behavior of the password reset endpoint.

## External consumers

None known.
