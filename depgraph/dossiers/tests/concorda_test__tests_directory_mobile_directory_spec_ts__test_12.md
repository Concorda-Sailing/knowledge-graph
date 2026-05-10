---
node_id: concorda-test::tests/directory/mobile-directory.spec.ts::test@12
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ac59d942346427109d8cb3108768e0c928bf95e91c1371325e7e60311ce06bdf
status: llm_drafted
---

# no horizontal overflow at 375px

## Purpose

This test suite validates the responsive behavior and layout integrity of the Member Directory page across mobile and desktop viewports. It ensures that mobile-specific UI elements (like the alphabet filter and view toggles) are correctly hidden and that the desktop-only table and headings are correctly rendered. It serves as a regression guard for viewport-dependent CSS classes (e.g., `hidden md:block`) and layout shifts.

## Invariants

- **Mobile viewport width is fixed at 375px** to test the narrowest common breakpoint.
- **Horizontal overflow must be $\le$ 376px** to ensure no side-scrolling occurs on mobile devices.
- **Mobile view must hide the `grid view`/`list view` buttons** and the alphabet filter.
- **Desktop view must show the `member directory` heading** and the table-based list view.
- **Member identity is verified via `h3` headings** within the `CardGrid` rather than data-attributes.

## Gotchas

- **Avoid using `data-slot` for selection.** Per commit `a2aa8e7`, the test was updated to select members by the `h3` heading inside the `CardGrid` because the codebase does not use `data-slot` attributes.
- **The mobile top bar uses a search input as a page-loaded signal.** The `waitForPage` helper relies on `page.getByPlaceholder(/search members/i)` to ensure the component has mounted before asserting on visibility or overflow.
- **Desktop list view requires an explicit click.** To verify the table renders, the test must explicitly click the `list view` button (commit `d96b171`).

## Cross-cutting concerns

- **Auth**: None (assumes page is accessible or uses existing session from setup).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: N/A.

## External consumers

None known.
