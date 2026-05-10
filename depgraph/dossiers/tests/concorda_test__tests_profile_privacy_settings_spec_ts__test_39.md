---
node_id: concorda-test::tests/profile/privacy-settings.spec.ts::test@39
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a83ba85e504aa5ba039f06d26fef40c18660417cd0f075e5fbde187a02e891aa
status: current
---

# can toggle show phone setting

## Purpose

Verifies the ability to toggle the visibility of the user's phone number within the Privacy settings tab. It ensures the UI switch (either a standard switch component or a labeled toggle) responds to user interaction and that the state can be toggled both on and off.

## Invariants

- **Requires the Privacy tab to be visible** before attempting to click it; the test uses a conditional check (`if (await privacyTab.isVisible())`) to avoid failures if the tab structure changes.
- **Uses a dual-selector strategy** for the phone toggle, looking for either a `switch` role filtered by text or a label containing "show phone" or "phone visible".
- **Expects a 500ms delay** after the first click to allow the UI state to settle before toggling back.

## Gotchas

- **Selector fragility:** The test relies on a complex `.or()` locator (line 48) to find the phone toggle. If the UI moves from a `switch` role to a standard checkbox or changes the label text, this test will fail to find the element.
- **Initial state dependency:** The test assumes the toggle is interactable. If the "Privacy" tab is not rendered or the phone setting is hidden behind a different permission level, the `if (await privacyTab.isVisible())` guard will silently skip the setup, potentially leading to false positives in the test run.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the Profile/Privacy settings.
- **Side effects**: Toggling this setting updates the user's profile visibility, which may affect how the user's contact information is surfaced in the directory/search results.

## External consumers

None known.
