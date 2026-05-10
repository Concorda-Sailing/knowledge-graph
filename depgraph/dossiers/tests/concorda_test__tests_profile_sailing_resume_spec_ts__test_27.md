---
node_id: concorda-test::tests/profile/sailing-resume.spec.ts::test@27
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d662d19e463889878a48a311351e7c6f40126bdad89a2c3a1d701a8286c4a833
status: llm_drafted
---

# can view experience level

## Purpose

Verifies that the "Experience Level" field is correctly rendered and visible on the user's profile. This test ensures that once the user navigates to the sailing-specific section of their profile, the seeded data (beginner, intermediate, advanced, or expert) is surfaced to the UI.

## Invariants

- **Relies on seeded data** — The test expects a specific value from a set of regex patterns (`/beginner|intermediate|advanced|expert/i`) to be present in the DOM.
- **Requires navigation state** — The element is only expected to be visible once the user has navigated to the correct sub-tab/section of the profile.
- **Timeout sensitivity** — Uses a 5,000ms timeout for visibility checks, assuming the component renders quickly once the tab is active.

## Gotchas

- **Selector fragility** — Recent history shows frequent adjustments to selectors to align with the actual UI. Per commit `7e8363c`, tests had to be adjusted because the web UI does not use an "inner profile Tabs" structure as previously assumed.
- **Layout dependency** — Per commit `5836d6a`, this test is sensitive to the "new profile layout" which changed how the sailing resume section is presented.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `api.login` in a parent `describe` or `beforeEach` block) to access the profile page.
- **Side effects**: Verifies the display of data that is typically seeded during the test setup phase.

## External consumers

None known.
