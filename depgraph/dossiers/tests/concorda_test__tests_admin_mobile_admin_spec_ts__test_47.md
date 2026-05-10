---
node_id: concorda-test::tests/admin/mobile-admin.spec.ts::test@47
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 80b38657f00b5edd6e6eab93b270159ca1b2a9a933911cfe3656a885b6a5d8ff
status: llm_drafted
---

# users page still shows desktop table

## Purpose

Ensures the desktop view of the Admin Users page remains functional and visible. It specifically verifies that the user table is not hidden by CSS (e.g., `display: none`) when the viewport width is set to a desktop-class width (1280px). This acts as a regression test to prevent responsive design changes from accidentally hiding critical admin tables on larger screens.

## Invariants

- **Viewport must be 1280x800.** The test explicitly sets `test.use({ viewport: { width: 1280, height: 800 } })` to ensure the desktop layout is triggered.
- **Table visibility is non-negotiable.** The test requires that at least one `role="table"` element has a computed style where `display` is not `none`.
- **Requires data loading completion.** The test relies on the `AdminListPage` loading state (spinner) resolving before asserting on the table's presence.

## Gotchas

- **Race condition on data load.** Per commit `02bd90c`, the test must explicitly wait for the heading and table to be visible to avoid failing while the `AdminListPage` is still in its loading/spinner state.
- **CSS-based hiding.** A simple `toBeVisible()` check is insufficient because the table might be in the DOM but hidden via CSS. The test uses `window.getComputedStyle(e).display !== 'none'` to ensure the table is actually rendered to the user.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (inherited from the file's setup/global-setup).
- **Side effects**: Changes to the responsive layout logic in `AdminListPage` or the global `md:hidden` utility classes will break this regression test.

## External consumers

None known.
