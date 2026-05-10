---
node_id: concorda-test::tests/profile/privacy-settings.spec.ts::test@16
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 13554c3ca1bd5220d8de218e24f97698ecf31845238d61805547b0206265db69
status: llm_drafted
---

# privacy section is accessible

## Purpose

Verifies that the privacy settings section is accessible and that specific visibility toggles (Directory and Phone) are present in the UI. This test ensures that users can navigate to the privacy tab and that the UI components for managing personal visibility are not broken or hidden by permission errors.

## Invariants

- **Navigation requires visibility check.** The test must verify `privacyTab.isVisible()` before attempting a `.click()` to avoid Playwright errors if the tab is not rendered.
- **Regex-based selection.** Uses case-insensitive regex (e.g., `/privacy/i`, `/directory/i`) to locate elements, allowing for slight variations in UI text.
- **Timeout threshold.** Asserts on visibility with a `5_000` ms timeout to account for network-idle delays during profile loading.

## Gotchas

- **Initial commit state.** Per commit `fd0c570`, this is part of the initial scaffolding of the Playwright E2E suite; the test patterns (like the `or` logic in the phone toggle) may be fragile if the underlying component library updates its accessibility labels.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the profile/privacy route.
- **Side effects**: Toggling the phone setting in the test (lines 46-55) simulates a state change that may affect how the user's profile is displayed to others in the directory.

## External consumers

None known.
