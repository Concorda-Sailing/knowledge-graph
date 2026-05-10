---
node_id: concorda-test::tests/dashboard/boats-panel.spec.ts::test@42
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 13147e4e5c723ab3026ac4be546d74e0706781fa90ef76459ca7aedf9756e0c3
status: llm_drafted
---

# My Crew tab is hidden when user owns no boats

## Purpose

Verifies the visibility logic for the "My Crew" tab in the dashboard when the user has no ownership rights. It ensures that the UI correctly hides the tab for users who are only crew members (e.g., `alice@test.concorda`) and do not own any boats, preventing a cluttered or confusing interface for non-owner viewports.

## Invariants

- **Requires a non-owner state.** The test relies on a user identity that has crew memberships but zero boat ownership to trigger the negative case.
- **Asserts on tab count.** The test expects the `getByRole('tab', { name: /^my crew$/i })` to return a count of `0` rather than just being invisible.
- **Navigation-driven.** The test must navigate to `/members` to trigger the component mounting and the subsequent visibility logic.

## Gotchas

- **URL routing changes.** Per commit `be406a9`, the dashboard recently transitioned to support new URL patterns (`?tab=boats&boat=`) alongside legacy routes; ensure the test still navigates to a path that triggers the correct component mounting for the "non-owner" view.
- **Component replacement.** The "boats panel" is a newer replacement for per-boat tabs (see commit `5720aac`); if the tab-switching logic is moved or renamed in the component, this test will fail to find the element.

## Cross-cutting concerns

- **Auth**: Relies on a pre-authenticated session for a user with specific permissions (crew-only, no ownership).
- **Side effects**: Affects the "My Crew" tab visibility on the `/members` dashboard route.

## External consumers

None known.
