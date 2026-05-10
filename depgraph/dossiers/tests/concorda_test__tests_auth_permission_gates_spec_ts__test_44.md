---
node_id: concorda-test::tests/auth/permission-gates.spec.ts::test@44
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 71731c1adc1acd4141d98852c2a5d8db5a6bab5e5b7e32d8c1524f85629c6e1f
status: current
---

# non-admin member sees "Access Denied" on /members/admin/users

## Purpose

Verifies that a non-admin user (specifically `USERS.alice`) is blocked from accessing the admin user management route. It ensures that even with a valid session, the UI correctly renders an "Access Denied" heading and prevents sensitive administrative elements like "create user" or "add user" from appearing in the DOM.

## Invariants

- **Requires valid authentication** via `api.login` and `api.acceptTos()` before navigation.
- **Uses `localStorage` injection** to set the `auth_token` on the Playwright `page` object.
- **Asserts on UI visibility** of the "access denied" heading and the absence of administrative actions.
- **Target URL is `/members/admin/users`**.

## Gotchas

- **Redirect target sensitivity**: Per commit `ba1c3bd`, the test relies on the correct unauth-redirect target behavior. If the redirect logic changes, the test may fail or hang on `waitForURL`.
- **Role-based visibility**: The test explicitly checks that `create user|add user` text is absent. If these strings are renamed in the UI components, this test will fail despite the permission gate working correctly.

## Cross-cutting concerns

- **Auth**: Depends on `api.login` and `api.acceptTos()` to establish a valid non-admin session.
- **Side effects**: Verifies the visibility of the admin user management interface.

## External consumers

None known.
