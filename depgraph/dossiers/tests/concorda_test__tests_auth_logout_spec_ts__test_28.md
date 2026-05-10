---
node_id: concorda-test::tests/auth/logout.spec.ts::test@28
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5e663ee3d9590e7b90d3070d6c3aa31a5ebd8f9bcc9e3edd1b4f525aba69ca4f
status: llm_drafted
---

# accessing /members after logout redirects to login

## Purpose

Verifies that the application correctly enforces session termination and protects sensitive routes. Specifically, it ensures that navigating to the `/members` area without an active session triggers a redirect to the authentication gateway (`/login` or `/join`). This test is distinct from the standard logout flow as it validates the security boundary of the protected `/members` route rather than just the UI button functionality.

## Invariants

- **Redirect target must be a regex match** for `/\/(login|join|$)/`.
- **Navigation must be unauthenticated**; the test starts by navigating directly to `/members` without a prior login step to ensure no session state is inherited from previous tests.
- **Timeout is 10,000ms** for both the `click` (in the preceding test) and the `waitForURL` to account for slow CI environments.

## Gotchas

- **UI Selector Fragility:** Per commit `f552929`, selectors must be strictly aligned with the actual UI (e.g., ensuring the "Sign Out" text is exact) to prevent test failures caused by minor text changes in the web component.
- **Navigation-based Auth Guard:** This test relies on the fact that the `/members` route is protected by a client-side or server-side guard that intercepts unauthenticated requests.

## Cross-cutting concerns

- **Auth**: Relies on the successful invalidation of the session/token to trigger the redirect.
- **Side effects**: Failure in this test indicates a regression in the auth guard, which would leave the `/members` route accessible to unauthenticated users.

## External consumers

None known.
