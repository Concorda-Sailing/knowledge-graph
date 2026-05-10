---
node_id: concorda-test::tests/profile/profile-info.spec.ts::test@12
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ab2cb38d7c5b80fe7480e444a956da6851e7d82ea4877e120d031ea9d1b0819e
status: llm_drafted
---

# profile page loads with user data

## Purpose

Verifies that the Profile Page correctly renders user data and allows for the modification of personal information fields (First Name and Phone Number). This test ensures that the "Edit" mode toggle and the subsequent "Save" action correctly persist changes to the user's profile via the UI.

## Invariants

- **Requires `ProfilePage` fixture**: The test relies on the `ProfilePage` class to handle navigation and initial state setup.
- **Edit mode is required for interaction**: Fields like `firstNameInput` and `#phone_number` are only visible/interactable after clicking the `.first()` edit button.
- **Uses regex for loose matching**: Selectors for "edit" and "save" buttons use case-insensitive regex (e.g., `/edit/i`) to avoid brittle text-matching failures.
- **Expects 5s visibility timeouts**: Input fields are asserted with a `5_000`ms timeout to account for the transition from view mode to edit mode.

## Gotchas

- **Selector alignment issues**: Recent commit `f552929` was required to "align selectors with actual UI" to fix broken tests during the initial green run.
- **Race conditions on Save**: The test uses `await page.waitForTimeout(1000)` after clicking the save button. This suggests the UI or the underlying API response has a slight delay before the field becomes editable again or the state updates.
- **Ambiguous "Edit" buttons**: The test uses `.first()` on the edit button (line 22) because the profile page contains multiple sections (Personal Info, etc.), and the test specifically targets the first one.

## Cross-cutting concerns

- **Auth**: Implicitly requires an authenticated session via the `ProfilePage.goto()` setup.
- **Side effects**: Modifies the user's profile data in the test database (First Name and Phone Number).

## External consumers

None known.
