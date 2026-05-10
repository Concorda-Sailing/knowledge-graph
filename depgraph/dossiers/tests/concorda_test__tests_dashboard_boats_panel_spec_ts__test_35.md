---
node_id: concorda-test::tests/dashboard/boats-panel.spec.ts::test@35
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 752a8b72b0aa8259beb953f89d40d705820ea256d7eb805adb5eed1685e1b259
status: current
---

# My Crew tab is visible to boat owner

## Purpose

Verifies that the "My Crew" tab is visible to a user when they are a boat owner. This test ensures that the dashboard navigation correctly reflects the user's relationship to their vessels, specifically checking for the presence of the tab in the member view.

## Invariants

- **Requires a user with boat ownership.** The test relies on the user context established in the parent `describe` block (implied to be an owner) to ensure the tab renders.
- **Tab visibility is tied to ownership.** The presence of the "My Crew" tab is a direct indicator of the user's status as a boat owner.

## Gotchas

- **URL routing is sensitive to query params.** Per commit `be406a9`, the dashboard now matches both the new `?tab=boats&boat=` pattern and the legacy route; ensure tests targeting the boats panel account for this dual-routing capability to avoid false negatives.
- **Navigation relies on `networkidle`.** As seen in the sibling test (line 30), the dashboard requires `await page.waitForLoadState('networkidle')` to ensure the tab-switching logic has completed before asserting visibility.

## Cross-cutting concerns

- **Auth**: Depends on the authenticated owner session established in the parent `describe` block.
- **Side effects**: The visibility of this tab affects the user's ability to navigate to crew-specific management views.

## External consumers

None known.
