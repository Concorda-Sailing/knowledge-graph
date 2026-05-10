---
node_id: concorda-test::tests/profile/privacy-settings.spec.ts::test@29
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5a7f4ce16c79757c925b79a7d16b4861fee0c1d357a68bf59299b9e87caa3492
status: current
---

# directory opt-in toggle is visible

## Purpose

Verifies that the "Directory Opt-in" toggle is visible within the Privacy settings tab. This test ensures that users can control their visibility in the organization's directory via the profile settings UI. It is a specific visibility check, distinct from the broader privacy content check in the preceding test.

## Invariants

- **Requires the Privacy tab to be active.** The test must first locate and click the `privacy` tab before asserting visibility of the toggle.
- **Uses regex for text matching.** The toggle is identified via a case-insensitive regex `/directory/i` to allow for variations in text casing.
- **Expects a 5,000ms timeout.** The visibility assertion relies on a 5-second window to account for potential network or rendering latency.

## Gotchas

- **Initial commit scaffolding.** Per commit `fd0c570`, this test is part of the initial E2E suite scaffolding; it is a baseline test and does not yet include complex state-change assertions (e.g., verifying the backend actually updates after the toggle is clicked).

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the profile/privacy settings page.
- **Side effects**: Successful toggling of this setting (if implemented in subsequent tests) affects the visibility of the user in the organization's directory.

## External consumers

None known.
