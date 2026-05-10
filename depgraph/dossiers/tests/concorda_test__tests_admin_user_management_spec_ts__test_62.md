---
node_id: concorda-test::tests/admin/user-management.spec.ts::test@62
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 209574644c7a76e7697d6533bd7f4c8b89083a39586b0e63a61fb0a8f78d17ee
status: llm_drafted
---

# can edit an existing user

## Purpose

Verifies the ability to modify existing user profiles via the Admin dashboard. It specifically tests the lifecycle of opening the edit dialog, verifying pre-filled data (e.g., the user's first name), and interacting with the password reset flow. This test ensures that the administrative UI correctly handles stateful transitions between the user list view and the modal dialogs.

## Invariants

- **Requires a pre-existing user** — The test relies on the existence of a user named 'alice' in the test database.
- **Uses `usersPage` fixture** — All interactions (searching, clicking edit, checking inputs) must go through the `usersPage` abstraction to maintain selector stability.
- **Dialog visibility** — The `dialogFirstNameInput` must be visible and contain the expected name before any cancellation or submission logic is executed.

## Gotchas

- **Search dependency** — Per commit `dad4d2e`, the test must explicitly `searchFor('alice')` before attempting to interact with the row or the edit button to ensure the user is visible in the current view.
- **UI Selector Fragility** — Per commit `f552929`, selectors for the "more/actions" menu and the password reset button are highly sensitive to text changes (e.g., `/more|actions|\.\.\./i`). If the UI text changes, the test will fail to find the action trigger.
- **Implicit timeouts** — The test uses `page.waitForTimeout(1000)` and `page.waitForTimeout(500)` to allow for UI transitions/animations. Removing these or reducing them may cause the `isVisible()` checks to fail in slower CI environments.

## Cross-cutting concerns

- **Auth**: Requires an authenticated Admin session (likely established via `api.login` in a parent `beforeEach` or `global-setup`).
- **Side effects**: Modifying a user's name or password via this flow affects the underlying user identity used in other authentication-related tests.

## External consumers

None known.
