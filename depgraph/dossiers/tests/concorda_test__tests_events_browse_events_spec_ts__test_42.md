---
node_id: concorda-test::tests/events/browse-events.spec.ts::test@42
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2ea12ba3b7f2f77cab11c8c92cee3ddf24cec228e4afa7565a16239a1fa094bd
status: llm_drafted
---

# member events page loads when authenticated

## Purpose

Verifies that the member-facing events view loads correctly under authenticated sessions. It ensures the `EventsPage` can navigate to `/members/events` without being intercepted by the authentication guard or redirected to the login page.

## Invariants

- **Requires authentication** — The test relies on a pre-authenticated state (likely via `storageState`) to avoid the login redirect.
- **Uses `EventsPage` abstraction** — Navigation is handled via `events.gotoMemberEvents()` rather than raw `page.goto`.
- **URL pattern match** — The test asserts that the final URL matches the regex `/\/members\/events/`.

## Gotchas

- **Selector fragility** — Per commit `f552929`, selectors must be aligned with the actual UI to avoid test failures; ensure any changes to the `EventsPage` class or the underlying component structure are reflected in the test-side selectors.

## Cross-cutting concerns

- **Auth**: Relies on an established authenticated session to bypass the login redirect.
- **Side effects**: Verifies the visibility of the member-specific event routing.

## External consumers

None known.
