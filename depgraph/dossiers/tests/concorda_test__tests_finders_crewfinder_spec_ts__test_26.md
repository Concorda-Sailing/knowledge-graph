---
node_id: concorda-test::tests/finders/crewfinder.spec.ts::test@26
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ec5b62e8e5282a547edc297ae0923a946a63ca6496df27ec62b1a0fd3e86d0a1
status: current
---

# view toggle switches between grid and list

## Purpose

Verifies the UI toggle functionality between grid and list views within the Crew Finder interface. It ensures that clicking the view buttons correctly updates the layout and that the transition between the two modes is stable.

## Invariants

- **View toggle availability**: Both `grid` and `list` buttons must be visible and interactable for the test to proceed.
- **Layout transition**: Switching from list to grid (and vice versa) must not trigger a hard crash or unhandled exception.
- **Selector stability**: The test relies on the presence of a `table` element to confirm the list view state.

## Gotchas

- **UI Drift/Layout Changes**: Per commit `5836d6a`, the "Go to Profile" CTA was removed from the empty state in favor of crew cards with direct links. This changed the navigation pattern from a single CTA to a link-based card system.
- **Selector Fragility**: Per commit `f552929`, selectors had to be realigned with the actual UI to fix the first successful green run.
- **Race conditions**: The test uses `page.waitForTimeout(500)` after clicking view toggles. This is a brittle way to wait for layout shifts and may fail if the environment is slow.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: None.

## External consumers

None known.
