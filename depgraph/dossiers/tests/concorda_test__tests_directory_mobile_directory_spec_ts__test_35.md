---
node_id: concorda-test::tests/directory/mobile-directory.spec.ts::test@35
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c8e91527aa9a36c2927629cf119a2837c7aa4fd60b0634e4175e1d6518dd64e1
status: current
---

# mobile card grid renders real member cards (not empty state)

## Purpose

Verifies that the mobile view of the Member Directory correctly renders a grid of member cards instead of an empty state or a table. It ensures that the `CardGrid` is visible and that the `HeroCard` components (identified by `h3` headings) are present, while simultaneously asserting that mobile-specific elements like the alphabet filter and the desktop-only table are hidden.

## Invariants

- **Mobile view must use a grid.** The test expects a `div.grid` containing `h3` elements for member names.
- **Empty state must be absent.** The test explicitly checks that the "no members found" heading is not present within the mobile-specific wrapper.
- **Desktop elements are hidden.** The `table` element and the alphabet filter must have a count of 0 in the mobile viewport.
- **Viewport dependency.** This test relies on the mobile viewport configuration to trigger the responsive-specific UI branches.

## Gotchas

- **Selection strategy changed from data-slots to semantic headings.** Per commit `a2aa8e7`, the test was updated to select members via `h3` headings rather than `data-slot` attributes, as the codebase has moved away from using `data-slot` for these identifiers.
- **Scoping is required for the empty state check.** Per commit `d96b171`, assertions must scope to the `parentWrapper` to ensure the "no members found" heading is truly absent from the mobile container and not just hidden elsewhere.

## Cross-cutting concerns

- **Auth**: None (assumes the page is loaded via a standard authenticated flow established in the test setup).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: The visibility of the `CardGrid` and the `h3` headings are critical for the mobile user experience in the directory.

## External consumers

None known.
