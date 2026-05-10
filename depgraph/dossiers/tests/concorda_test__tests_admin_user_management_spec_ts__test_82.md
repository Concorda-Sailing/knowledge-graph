---
node_id: concorda-test::tests/admin/user-management.spec.ts::test@82
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4098a1ac745bfdd2b87e13ab5876ebef9f2443668634e9150624f465d129df93
status: llm_drafted
---

# can open change password dialog

## Purpose

Verifies the ability of an administrator to trigger the password change dialog for a specific user. This test ensures that the UI correctly surfaces the password reset/change option within the user's action menu and that the resulting input field is visible and interactable.

## Invariants

- **Requires a visible user row** — The test must first search for and locate a user (e.g., 'alice') to ensure the action menu is available.
- **Action menu is conditional** — The test must check for the existence of the `moreButton` (the `...` or `actions` button) before attempting to click it, as the menu is not always present in the DOM.
- **Regex-based selection** — The password action is identified via a case-insensitive regex (`/password|reset.*password/i`) to accommodate different UI label variations.

## Gotchas

- **Search dependency** — Per commit `dad4d2e`, the test must explicitly search for the user (e.g., `usersPage.searchFor('alice')`) before attempting to open the dialog, otherwise the user row will not be present in the viewport.
- **UI Selector Fragility** — Per commit `f552929`, the selectors for the action menu and password input are highly sensitive to UI changes; the test relies on `getByRole('button', { name: /more|actions|\.\.\./i })` to find the dropdown trigger.

## Cross-cutting concerns

- **Auth**: Requires an active Administrator session to access the `usersPage`.
- **Side effects**: Successful interaction with this dialog (if completed) would trigger a password change in the production-seeded database.

## External consumers

None known.
