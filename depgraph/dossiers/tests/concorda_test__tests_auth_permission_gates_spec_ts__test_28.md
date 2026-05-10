---
node_id: concorda-test::tests/auth/permission-gates.spec.ts::test@28
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8ddb02e96bf9501372dcf43f372cfe211c4abe8a360f5cdce6430f9af925baa8
status: llm_drafted
---

# unauthenticated visit to a deep member route redirects to /login

## Purpose

Verifies the routing and authorization logic for unauthenticated and unauthorized users. It ensures that the `AuthProvider` correctly intercepts requests to protected routes (like `/members` or `/members/crewfinder`) and redirects them to `/login` with the appropriate `?redirect=` query parameter. It also validates that non-admin users are blocked from accessing administrative views via an "Access Denied" UI state.

## Invariants

- **Unauthenticated redirection**: Visiting a protected route without a token must trigger a redirect to `/login`.
- **Redirect preservation**: The `?redirect=` parameter must contain the URI-encoded original path to allow post-login landing.
- **Admin gate**: Users with a valid token but insufficient permissions must see an "Access Denied" heading and must not be able to see administrative-only UI elements (e.g., "create user").
- **Token injection**: Tests use `localStorage.setItem('auth_token', ...)` to simulate authenticated sessions within the browser context.

## Gotchas

- **Redirect target normalization**: Per commit `ba1c3bd`, the redirect target logic was recently fixed to ensure proper normalization for users like `sole-owner-Bob`.
- **Auth state dependency**: Tests rely on `api.acceptTos()` being called after login to ensure the user state is fully initialized before attempting to access protected routes.

## Cross-cutting concerns

- **Auth**: Directly tests the interaction between `AuthProvider` and the routing layer.
- **Side effects**: Validates that administrative UI components (e.g., "create user" buttons) are not rendered in the DOM when the user lacks permissions.

## External consumers

None known.
