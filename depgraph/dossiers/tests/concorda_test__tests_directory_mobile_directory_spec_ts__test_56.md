---
node_id: concorda-test::tests/directory/mobile-directory.spec.ts::test@56
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ef6390eddeba537b0ba49875c4ce4dada99ba63c612d277c14cb1f662f413737
status: current
---

# view toggle visible on desktop

## Purpose

Verifies that the Member Directory UI correctly adapts to desktop viewports. It ensures that the "Grid View" and "List View" toggle buttons, as well as the alphabet filter, are visible and functional when the viewport width is set to 1280x800. This test is distinct from the mobile-specific tests which assert that these elements are hidden to preserve screen real estate.

## Invariants

- **Viewport requirement**: Must use `test.use({ viewport: { width: 1280, height: 800 } })` to trigger the desktop-specific CSS media queries.
- **Heading visibility**: The `heading` with name `/member directory/i` must be visible to confirm the page loaded correctly.
- **List view fallback**: When "List View" is clicked, a `role="table"` must be present in the DOM.

## Gotchas

- **Selector fragility**: Recent commit `a2aa8e7` and `0376925` highlight that the directory does not use `data-slot` attributes for selection; instead, elements must be selected via `h3` headings or specific ARIA roles.
- **Responsive visibility**: The alphabet filter and view toggles are intentionally hidden on mobile; if these tests fail in a CI environment, check if the viewport width is being correctly overridden by a global setup.

## Cross-cutting concerns

- **Auth**: None (assumes authenticated session is established via global setup/Playwright fixtures).
- **Websocket**: None.
- **Audit**: None.
- **Rate limit**: None.
- **Side effects**: None.

## External consumers

None known.
