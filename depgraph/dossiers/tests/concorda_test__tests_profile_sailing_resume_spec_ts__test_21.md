---
node_id: concorda-test::tests/profile/sailing-resume.spec.ts::test@21
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bcf8d00dc2adb3f049af9baf8e1d4521e4e86d4b29b60b9f55cdce491e6b0c8e
status: current
---

# sailing resume section is visible

## Purpose

Verifies the visibility and basic interaction of the "Sailing Experience" section within the user profile. This test ensures that the sub-tab navigation works correctly and that the seeded data for experience levels and preferred positions is rendered as expected. It serves as a regression check for the profile layout, specifically targeting the transition from a flat profile to a tabbed interface.

## Invariants

- **Requires tab activation.** The "Sailing Experience" content is nested within a `TabsTrigger` (role=tab) and is not visible in the DOM until the tab is clicked.
- **Relies on seeded data.** The test expects specific strings (e.g., "beginner", "trimmer", "bowman") to be present, which are driven by the test user's profile data.
- **Uses a 10s visibility timeout.** Due to the asynchronous nature of tab switching and network idle states, the `sailingTab` requires a higher timeout than standard element visibility.

## Gotchas

- **UI Drift (Layout Change).** Per commit `5836d6a`, the "Sailing Experience" is no longer a top-level section but a sub-tab inside the profile. Tests must click the tab to reveal the content.
- **Selector Fragility.** Recent fixes in `7e8363c` and `f552929` were required to align selectors with the actual web UI, specifically because the profile no longer uses an "inner profile Tabs" pattern.
- **Race conditions on "About Me" edits.** The `can edit about me field` test uses a `page.waitForTimeout(1000)` after clicking save; this is a brittle way to handle the async save operation and may need replacement with a more robust state-check if the API latency increases.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely established via `api.login` in a parent `describe` block or `beforeEach`).
- **Side effects**: Changes to the "About Me" field (if the test is run) update the user's profile record in the database.

## External consumers

None known.

## Open questions

- Should the "About Me" edit test use a more robust assertion (like waiting for a network response or a specific UI success toast) instead of the hardcoded `waitForTimeout(1000)`?
