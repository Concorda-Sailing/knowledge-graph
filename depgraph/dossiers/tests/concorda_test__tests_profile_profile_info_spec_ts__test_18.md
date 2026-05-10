---
node_id: concorda-test::tests/profile/profile-info.spec.ts::test@18
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c8e5faa9719175037c4019fa7ae4d0d41238c7e01bdc6318fc02f94bb16dddaa
status: current
---

# can edit name fields

## Purpose

Verifies the end-to-end (E2E) functionality of the user profile editing flow. It ensures that users can successfully transition from viewing profile data to an editable state and back, specifically testing the mutation of name fields and phone numbers. This test is critical for ensuring that the "Personal Information" section of the profile remains interactive and that state changes (like reverting a name change) persist correctly in the UI.

## Invariants

- **Requires `page.waitForLoadState('networkidle')`** before interacting with edit buttons to ensure the profile data has loaded.
- **Uses `getByRole('button', { name: /edit/i }).first()`** to target the Personal Information section specifically, as multiple sections may exist on the page.
- **Input fields must be cleared before filling** (`firstNameInput.clear()`) to prevent appending text to existing values.
- **Requires a manual `page.waitForTimeout(1000)`** after clicking "Save" to allow the asynchronous state update and UI transition to complete before attempting to re-enter edit mode.

## Gotchas

- **Selector Fragility:** Per commit `f552929`, selectors had to be realigned with the actual UI to achieve a "green run." Avoid using generic text selectors that might overlap with other profile sections (e.g., "Address" or "Preferences").
- **Race Conditions:** The test relies on a hardcoded 1-second sleep after saving. If the API response or UI re-render takes longer than 1000ms, the subsequent `editButton.click()` will fail because the element is not yet actionable.

## Cross-cutting concerns

- **Auth**: Depends on the authenticated session established in the `profile.goto()` setup (likely via `api.login` or a similar fixture).
- **Side effects**: Successful execution of these tests validates the data integrity for the user's profile, which is surfaced in the user settings and dashboard views.

## External consumers

None known.
