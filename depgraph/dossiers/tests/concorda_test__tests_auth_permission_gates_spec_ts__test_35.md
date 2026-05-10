---
node_id: concorda-test::tests/auth/permission-gates.spec.ts::test@35
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6b9fde185d30910db52b2727c6192514ed88471c0f11e6d8867b19266657d5dc
status: current
---

# garbage token is rejected and triggers redirect

## Purpose

Verifies that the application correctly handles unauthorized access attempts by enforcing redirects and permission-based visibility. It ensures that unauthenticated users are redirected to `/login` (preserving the intended path via `?redirect=`) and that users with insufficient privileges (e.g., non-admins) are blocked from accessing sensitive routes like `/members/admin/users`.

## Invariants

- **Redirect behavior**: Unauthenticated visits to deep routes must trigger a redirect to the login page.
- **Token validation**: Providing a malformed or "garbage" token in `localStorage` must result in a redirect to the login page rather than a broken state.
- **Role-based visibility**: Non-admin users must see an "Access Denied" heading and must not see administrative UI elements (e.g., "create user" or "add user" text).
- **State persistence**: The test relies on `localStorage.setItem('auth_token', ...)` to simulate a logged-in state for permission testing.

## Gotchas

- **Redirect target preservation**: Per commit `ba1c3bd`, the system must ensure that the `?redirect=` parameter correctly preserves the original path so the user lands on the intended destination after a successful login.
- **Admin UI masking**: When testing non-admin access, it is not enough to check for the "Access Denied" message; the test must also explicitly assert that administrative buttons/text (like "create user") are not present in the DOM to ensure the content is truly blocked.

## Cross-cutting concerns

- **Auth**: Uses `localStorage` to inject tokens; relies on the `ApiClient` and `USERS` constants for valid credential injection.
- **Side effects**: Verifies the behavior of the routing engine and the permission-gate middleware.

## External consumers

None known.
