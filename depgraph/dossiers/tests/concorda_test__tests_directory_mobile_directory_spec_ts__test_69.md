---
node_id: concorda-test::tests/directory/mobile-directory.spec.ts::test@69
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b0b6250120ca41e60ef79ae23061d9427a97ea3906e8dcb43eb4f7469adc8c92
status: llm_drafted
---

# desktop list view renders a real table

## Purpose

Verifies that the Member Directory correctly transitions to a desktop-optimized table view. It ensures that when a user clicks the "list view" toggle, the UI renders a semantic `<table>` with the expected column headers (`name` and `email`) rather than the default mobile-optimized card layout.

## Invariants

- **Navigation requirement**: The test must first navigate to `/members/directory` before attempting to toggle the view.
- **View transition**: The test relies on the presence of a button with the accessible name `/list view/i` to trigger the layout change.
- **Semantic structure**: A successful test requires the presence of a `<table>` element and specific `columnheader` roles for both `name` and `email`.

## Gotchas

- **Selector fragility**: Recent changes (commit `a2aa8e7`) indicate that the directory components have moved away from `data-slot` attributes in favor of selecting by `h3` headings. Ensure assertions on member cards or list items do not rely on deprecated data attributes.
- **Layout regression**: As noted in commit `d96b171`, the desktop list view is susceptible to regressions where the table might fail to render or the toggle might not trigger the expected layout shift.

## Cross-cutting concerns

- **Auth**: None (assumes authenticated session established by previous setup/test steps).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: N/A.

## External consumers

None known.
