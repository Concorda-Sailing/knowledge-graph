---
node_id: concorda-test::pages/login.page.ts::LoginPage.loginAndWait
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3d72f571c412d6c9265b87cb0859cf4872d42357c9cb872a6f89c80871f329e8
status: current
---

# LoginPage.loginAndWait

## Purpose

The high-level helper for performing a full authentication flow in E2E tests. Unlike `login()`, which only performs the input and click actions, `loginAndWait()` waits for the navigation to complete by asserting the URL matches the `**/members**` pattern. Use this when the test requires a guaranteed post-login state before proceeding to subsequent page interactions.

## Invariants

- **Requires a preceding `goto('/login')` call** to ensure the browser is on the correct starting page before attempting to fill credentials.
- **Implicitly waits for navigation** to the `/members` path via `this.page.waitForURL('**/members**')`.
- **Uses standard text input** for `email` and `password` via the `LoginPage` element locators.

## Gotchas

- **Initial scaffolding only.** Per commit `fd0c570`, this is part of the initial E2E suite scaffolding; it lacks advanced error handling or retry logic for flaky network conditions during the redirect.

## Cross-cutting concerns

- **Auth**: Triggers the full UI-driven authentication flow, transitioning the session from unauthenticated to a member-authenticated state.
- **Side effects**: Successful completion of this method is a prerequisite for any tests interacting with member-only views (e.g., the members dashboard).

## External consumers

None known.
