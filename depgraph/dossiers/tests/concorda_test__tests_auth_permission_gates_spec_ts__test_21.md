---
node_id: concorda-test::tests/auth/permission-gates.spec.ts::test@21
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0d9bebb63ef2878a886c8c11fdf0953675a4ede70f6e325ca4453d4fb0eb8bfc
status: llm_drafted
---

# unauthenticated visit to /members redirects to /login

## Purpose

Verifies the redirection logic and permission-based access control of the web app. It ensures that unauthenticated users are redirected to `/login` with a preserved `?redirect=` parameter, and that users without sufficient permissions (e.g., non-admins) are blocked from sensitive routes by an "Access Denied" UI. This test suite validates the interaction between the `AuthProvider` and the routing layer.

## Invariants

- **Unauthenticated users must be redirected to `/login`**. The `AuthProvider` (from `contexts/auth-context.tsx`) must intercept requests to protected routes like `/members`.
- **The `?redirect=` parameter must be preserved**. The URL must contain the encoded original path to allow post-login resumption of the user's journey.
- **Non-admin users must see an "Access Denied" card**. If a user's permissions lack the required `admin.*` entry, the admin layout must render the error state instead of the protected content.
- **Protected content must not leak**. For admin routes, the test asserts that specific admin-only text (e.g., "create user") is not present in the DOM for non-admin users.

## Gotchas

- **Redirect target changed on 2026-04-XX**. Per the source comment, the redirect target was moved from `/join` to `/login` to prevent existing members from being accidentally funneled into the registration flow when clicking pricing links.
- **Manual token injection is required for "garbage token" tests**. To test rejection of invalid credentials, the test must manually set `localStorage.setItem('auth_token', ...)` before navigating, as the `AuthProvider` relies on this state.

## Cross-cutting concerns

- **Auth**: Relies on `AuthProvider` in `contexts/auth-context.tsx` to trigger the redirect logic.
- **Side effects**: Validates the "Access Denied" UI state used by the admin layout when `user.permissions` is insufficient.

## External consumers

None known.
