---
node_id: concorda-test::tests/auth/logout.spec.ts::test@6
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 73d17ddc8b22f14c0dd7088240e7c0cb8d54d3e58e04143ef8d2021235e4d86d
status: llm_drafted
---

# logout clears auth and redirects to login

## Purpose

Verifies the end-to-end logout flow and ensures that authenticated sessions are properly terminated. It tests two distinct behaviors: first, that a user can navigate to the "My Profile" tab and click the "Sign Out" card to be redirected; second, that direct navigation to protected routes (like `/members`) after logout results in a redirect to the login or join pages.

## Invariants

- **Sign Out is a `div` element**, not a button or a link.
- **The "Sign Out" element is located within the "My Profile" tab**, which must be visible before the sign-out action can be performed.
- **Successful logout results in a redirect** to a URL matching the pattern `/\/(login|join|$)/`.

## Gotchas

- **The UI structure is volatile.** Per commit `7e8363c`, tests must account for the absence of "inner profile Tabs" in the current web UI.
- **The "Sign Out" element is a clickable `div`**, not a standard button. Tests must use `page.getByText('Sign Out', { exact: true })` and `scrollIntoViewIfNeeded()` to ensure the element is interactable before clicking.
- **Navigation timing is sensitive.** The test relies on `page.waitForURL` with specific timeouts (10-15s) to account for the transition from authenticated state to the redirect destination.

## Cross-cutting concerns

- **Auth**: Verifies the destruction of the session and the effectiveness of the redirect-to-login guard for protected routes like `/members`.
- **Side effects**: Ensures that the user's authenticated state is cleared, preventing unauthorized access to the dashboard or member areas.

## External consumers

None known.
