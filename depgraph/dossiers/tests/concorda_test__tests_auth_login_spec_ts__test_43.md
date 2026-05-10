---
node_id: concorda-test::tests/auth/login.spec.ts::test@43
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0912a19e6ac56302861c3cae616a643058645c15a1d05936b8d1fc4b30652638
status: current
---

# forgot password link navigates correctly

## Purpose

Verifies that the "Forgot Password" link correctly redirects the user to the password recovery flow. This test ensures that the navigation path from the login page to the `/forgot-password` route is functional and that the link is reachable.

## Invariants

- **Navigation target is `/forgot-password`** — the test asserts that the URL matches this specific path after clicking the link.
- **Relies on `loginPage` fixture** — the test assumes the `loginPage` object is correctly initialized with the `forgotPasswordLink` locator.

## Gotchas

- **Initial scaffolding only** — per commit `fd0c570`, this is part of the initial E2E suite scaffolding. Tests in this file are currently high-level and may not yet cover deep edge cases of the recovery flow, only the presence of the link and the resulting URL change.

## Cross-cutting concerns

- **Auth**: Indirectly validates the entry point for the password recovery/reset flow.
- **Side effects**: None.

## External consumers

None known.
