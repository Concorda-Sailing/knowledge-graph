---
node_id: concorda-test::tests/boats/mobile-boat-resume.spec.ts::test@27
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a3cee596c86ade7f395cce52711c384ba4eb376ef0a8e628d921df5815803c2e
status: llm_drafted
---

# hero action buttons visible on mobile (no hover required)

## Purpose

Verifies that critical action buttons (specifically "Add Banner" or "Change Banner") are visible to boat owners on mobile viewports without requiring a hover state. This ensures that the "hero" actions are immediately accessible in the mobile-optimized UI.

## Invariants

- **Requires `goToFirstOwnedBoat(page)`** to establish the correct authenticated context before checking visibility.
- **Buttons must be visible without hover** — the test specifically checks for the presence of the banner buttons to ensure they aren't hidden behind hover-only CSS rules.
- **Conditional check on button existence** — the test uses a count check (`await bannerBtn.count() > 0`) to avoid failing if the specific banner UI is not rendered in the current test state.

## Gotchas

- **`overview` tab is a no-op** — per commit `a48c539`, the `overview` tab is the default active tab. Clicking it is a no-op and can cause locator flakiness when the tablist is scrolled out of view; the test explicitly skips the click for this tab.
- **Profile content relocation** — per commit `ba1c3bd`, the `profile` tab was removed as a top-level tab. Its content is now nested within the `overview` tab (see `boat-owner-view.tsx`), so tests must not attempt to click a "Profile" tab.

## Cross-cutting concerns

- **Auth**: Relies on `goToFirstOwnedBoat` to set up the authenticated session.
- **Side effects**: Changes to the mobile tab bar layout or the "Profile" tab structure (as seen in `ba1c3bd`) will break the iteration logic in the sibling tests within this file.

## External consumers

None known.
