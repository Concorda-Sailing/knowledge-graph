---
node_id: concorda-test::tests/directory/mobile-directory.spec.ts::test@63
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c7491d44d7ed796bdc2c86125867b90479abe85e1a8df4aa5291173d97df67c7
status: current
---

# alphabet filter visible on desktop

## Purpose

Verifies that the alphabet filter (A-Z/M navigation) is visible on desktop viewports. This test ensures that the UI remains functional for users navigating large directories via letter-based filtering.

## Invariants

- **Viewport requirement**: Requires a desktop-class viewport (width 1280, height 800) to ensure the filter is not hidden by mobile-specific CSS or media queries.
- **Navigation target**: Must navigate to `/members/directory` before asserting visibility.
- **Element identity**: The filter is identified by a button role with a regex name matching the specific letter (e.g., `/^M$/`).

## Gotchas

- **Visibility logic**: Per commit `6b3e660`, the alphabet filter is intentionally hidden on medium and small screens (`<md`) and only becomes visible on medium and up (`>=md`). If this test fails in a CI environment with a smaller viewport, check the media query/breakpoint logic.
- **Heading dependency**: The test relies on the presence of the "Member Directory" heading to confirm the page has loaded correctly before checking the filter.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: N/A.

## External consumers

None known.
