---
node_id: concorda-test::tests/boats/mobile-boat-resume.spec.ts::test@42
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 50a2789eff44ea03311d078cedab36a5b1404004def774701334c620ee301664
status: llm_drafted
---

# (unnamed)

## Purpose

Verifies that the boat resume view remains responsive on mobile viewports by checking that each tab's content fits within a 376px width. It iterates through the remaining top-level tabs (excluding 'overview') to ensure that scrolling to a tab and selecting it does not cause horizontal overflow or layout breakage.

## Invariants

- **Viewport width limit is 376px.** The test asserts that `document.documentElement.scrollWidth` is less than or equal to this value to simulate a standard mobile device width.
- **Tabs must be scrolled into view.** The test uses `tab.scrollIntoViewIfNeeded()` to ensure the element is reachable before interaction.
- **'overview' is the default active tab.** The loop skips the `.click()` action for the 'overview' tab because it is already active by default and clicking it can cause locator flakiness.

## Gotchas

- **Avoid clicking the default tab.** Per commit `a48c539`, clicking the 'overview' tab is a no-op and can lead to flaky locator behavior if the tab is scrolled out of the horizontal list.
- **Profile tab is no longer a top-level tab.** Per commit `ba1c3bd`, the 'profile' tab was removed as a top-level entry; its content is now nested within the 'overview' tab. Tests must only iterate through the remaining valid tabs: `['overview', 'details', 'photos', 'punchlist', 'documents', 'positions']`.
- **Sticky header interference.** The test explicitly calls `window.scrollTo(0, 0)` before interacting with tabs to ensure the sticky tab bar does not obstruct the viewport or interfere with the `scrollIntoViewIfNeeded` call.

## Cross-cutting concerns

- **Auth**: Requires a successful session via `goToFirstOwnedBoat(page)`.
- **Side effects**: Ensures the mobile layout for boat detail views (specifically the tab bar and hero actions) remains within the horizontal bounds of a mobile viewport.

## External consumers

None known.
