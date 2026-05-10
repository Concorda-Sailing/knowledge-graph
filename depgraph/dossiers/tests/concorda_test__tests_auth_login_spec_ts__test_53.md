---
node_id: concorda-test::tests/auth/login.spec.ts::test@53
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0aafe0323f400bd02e4cac572296a471fdfef9462f70c8f2250dde075d362fb9
status: current
---

# show/hide password toggle works

## Purpose

Verifies the UI-level behavior of the password visibility toggle on the login page. It ensures that clicking the eye icon correctly toggles the `type` attribute of the password input between `password` and `text`.

## Invariants

- **Input type transition**: The `loginPage.passwordInput` must transition from `type="password"` to `type="text"` upon clicking the toggle button.
- **Locator structure**: The toggle button is a sibling/child of the `#password` input, specifically accessed via `locator('#password').locator('..').locator('button')`.

## Gotchas

- **Initial state dependency**: The test assumes the input starts as `type="password"` (per line 55) before the interaction occurs.

## Cross-cutting concerns

- **Auth**: Indirectly validates the UI state of the authentication entry point.
- **Side effects**: None.

## External consumers

None known.
