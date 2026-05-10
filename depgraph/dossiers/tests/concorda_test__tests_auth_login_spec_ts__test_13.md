---
node_id: concorda-test::tests/auth/login.spec.ts::test@13
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2404f364173d05562405cc9348414ec631a34d2c53c4a6183878f76981eaa981
status: current
---

# page loads with expected elements

## Purpose

Verifies the fundamental UI and navigation properties of the Login page. It ensures that essential input fields (email, password), action buttons (sign in, forgot password, register), and the password visibility toggle are present and functional. This serves as the baseline smoke test for the authentication entry point.

## Invariants

- **Requires `LoginPage` instance.** The test relies on the `LoginPage` class to abstract selectors like `emailInput` and `passwordInput`.
- **Navigation is URL-driven.** Successful authentication must result in a redirect to a path matching `**/members**`.
- **Form validation is client-side.** The "empty form" test relies on HTML5 validation behavior to prevent submission when required fields are empty.

## Gotchas

- **Initial commit state.** Per commit `fd0c570`, this is part of the initial E2E suite scaffolding; the tests currently focus on high-level element visibility and basic navigation rather than deep state verification.

## Cross-cutting concerns

- **Auth**: Directly tests the UI-to-API interaction for the login flow.
- **Side effects**: Successful login (as seen in the redirect to `/members`) is the prerequisite for all authenticated user sessions in the system.

## External consumers

None known.
