---
node_id: concorda-test::tests/profile/profile-info.spec.ts::test@44
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b5ee1393d829992bd2e601a4abaea1ff51fa07276fbe24f7a8f1bcc8b7bbbee2
status: current
---

# can edit phone number

## Purpose

Verifies the ability to edit and revert a user's phone number within the Personal Information section of the profile. This test ensures that the `#phone_number` input field is interactive and that changes persist through a save-and-re-edit cycle.

## Invariants

- **Input field ID is `#phone_number`**. The test relies on this specific ID to target the phone input.
- **Requires a two-step verification**. The test must click the "Edit" button, modify the value, save, and then re-click "Edit" to verify the change or revert it.
- **Uses `.first()` on button selectors**. The test assumes multiple "Save" or "Edit" buttons may exist on the page, specifically targeting the first instance found.

## Gotchas

- **Selector instability**. Per commit `f552929`, selectors had to be aligned with the actual UI to fix the first green run; ensure any changes to the profile form use stable, non-ambiguous selectors.
- **Race conditions on save**. The test uses `await page.waitForTimeout(1000)` after clicking save to allow the UI to settle before attempting to re-enter edit mode.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the profile edit views.
- **Side effects**: Updates the user's profile record in the database.

## External consumers

None known.
