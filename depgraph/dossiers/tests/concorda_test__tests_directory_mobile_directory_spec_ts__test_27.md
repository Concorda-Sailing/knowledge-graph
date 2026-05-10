---
node_id: concorda-test::tests/directory/mobile-directory.spec.ts::test@27
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 56e255063b7be433a28b49819a1702b901c2a6851eb0a0ab3b011939e41eb3ce
status: current
---

# alphabet filter is hidden on mobile

## Purpose

Verifies that the alphabet filter (the A-Z navigation row) is correctly hidden from the DOM when the viewport is in mobile mode. This ensures that mobile users are not overwhelmed by the large button row and that the UI remains uncluttered on smaller screens.

## Invariants

- **Target element is a button** — The test specifically looks for a button with the name matching a single letter (e.g., `^M$`).
- **Visibility is absolute** — The test asserts `toHaveCount(0)` rather than just checking for invisibility, ensuring the element is not just hidden via CSS but absent from the accessibility tree/DOM.
- **Viewport dependency** — This test relies on the implicit mobile viewport settings of the test runner or the global configuration for the `mobile-directory` suite.

## Gotchas

- **Avoid `data-slot` attributes** — Per commit `a2aa8e7`, the test suite has moved away from selecting member cards via `data-slot` attributes. Instead, it uses semantic selectors like `h3` headings to ensure the UI is actually accessible and readable.
- **Heading-based selection** — As noted in commit `a2aa8e7`, the test must select members by their `h3` heading to remain robust against changes in the underlying data structure.

## Cross-cutting concerns

- **Auth**: None (assumes authenticated session is established by the test runner/global setup).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Changes to the directory component's responsive logic will break this test (specifically the visibility of the alphabet filter).

## External consumers

None known.
