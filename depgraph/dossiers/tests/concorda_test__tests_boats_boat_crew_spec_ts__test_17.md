---
node_id: concorda-test::tests/boats/boat-crew.spec.ts::test@17
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8900fe78caac9a1c307bfa03d0d36a5397453d08262e1b60e686cc20e7c1f573
status: current
---

# crew tab is accessible

## Purpose

Verifies that the "Crew" tab is accessible and that users can initiate the invite flow via email. It ensures the UI correctly displays the crew list (or empty state) and that the invitation dialog/email input is functional. This test is part of the boat-level management suite, ensuring that membership expansion via email works as expected.

## Invariants

- **Tab visibility is conditional.** The test checks `if (await crewTab.isVisible())` before attempting to click, as the tab may not be present in all boat configurations.
- **Input field selection is polymorphic.** The email input can be identified by either a `Label` or a `Placeholder` to account for different UI implementations.
- **Success state is text-based.** The test looks for specific success strings (e.g., "invited" or the user's name) to confirm the action completed.

## Gotchas

- **Requires explicit waits for UI stability.** The test uses `await page.waitForTimeout(1000)` and `await page.waitForTimeout(2000)` around the invite button and email submission. This is a fragile pattern; per commit `0990b5d`, these delays were likely added to handle race conditions in the invite flow, but they increase test duration.
- **Implicit dependency on networkidle.** The test relies on `await page.waitForLoadState('networkidle')` after clicking the tab to ensure the crew list/dialog is actually ready for interaction.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via a boat-owner or admin role) to see the "Invite" button and the "Crew" tab.
- **Side effects**: Successful execution of the invite flow triggers a crew-request/invite event in the backend, which should eventually update the boat's member list.

## External consumers

None known.
