---
node_id: concorda-test::tests/admin/mobile-admin.spec.ts::test@6
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4a13328e8cf2b318df17c49525770404ee0416ea5ae1497027350a782ce82059
status: llm_drafted
---

# users page renders mobile card list, no visible table

## Purpose

Verifies the responsive behavior of the Admin Users page, specifically ensuring that the UI switches from a desktop table to a mobile card list when the viewport width is small. It validates that the "Add User" dialog remains within the mobile viewport bounds and that the page does not suffer from horizontal overflow. This test ensures that the mobile-first layout logic (using Tailwind's `md:` prefix) is functioning correctly for administrative workflows.

## Invariants

- **Viewport-driven layout**: The mobile suite must use a `375x812` viewport to trigger the `.md:hidden` card list visibility.
- **Data-load dependency**: Assertions on the card list or the "Add User" button must wait for the heading to be visible to ensure the asynchronous data fetch has completed.
- **Desktop regression**: The desktop suite must verify that the `<table>` element is not just present in the DOM, but has a `display` style other than `none`.
- **Overflow limit**: The document `scrollWidth` must not exceed the viewport width plus a small buffer (376px) to ensure no horizontal scrolling is triggered on mobile.

## Gotchas

- **Race condition on data load**: Per commit `02bd90c`, assertions on the mobile card list or the "Add User" button fail if they don't explicitly wait for the page heading to appear first. This prevents tests from failing while the component is still in a loading state.
- **Visibility vs. Presence**: Simply checking for the existence of a table is insufficient for the desktop regression; per the logic in `visibleTables`, one must evaluate `window.getComputedStyle(e).display` to ensure the table isn't hidden by a CSS class.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (implicitly handled by the test runner's setup/global-setup).
- **Side effects**: Changes to the mobile layout or the `md:` breakpoint logic will break the `users page renders mobile card list` and `admin dialog fits within viewport` tests.

## External consumers

None known.
