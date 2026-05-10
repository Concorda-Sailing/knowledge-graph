---
node_id: concorda-test::tests/admin/mobile-admin.spec.ts::test@35
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 248716b8518a2b2a6bdaa55db656e453ef3de333f7aca14c9a5a955bf9b17ad8
status: llm_drafted
---

# no horizontal overflow on admin users page

## Purpose

Verifies that the admin user management page maintains a responsive layout on mobile viewports. Specifically, it ensures that the page does not exhibit horizontal overflow (exceeding a 376px width) when viewed on a narrow screen, preventing broken UI in the mobile admin experience.

## Invariants

- **Viewport width limit:** The `document.documentElement.scrollWidth` must be $\le 376$ to pass.
- **Heading visibility:** The test requires the `heading` with name `/users/i` to be visible before checking overflow to ensure the page has actually loaded.
- **Mobile-specific elements:** The test expects a `.md:hidden > div.rounded-lg.border` element to be visible, which represents the mobile-optimized card layout.

## Gotchas

- **Data loading latency:** Recent commit `02bd90c` added a requirement to wait for data loading before assertions. If the test checks `scrollWidth` before the component finishes rendering, it may pass or fail incorrectly based on the initial empty state.
- **Desktop regression:** The `desktop admin (regression)` block exists because changes to mobile layouts (like the `card-list` mentioned in commit `625d101`) can inadvertently hide or break the table view on larger screens.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (inherited from the `mobile-admin.spec.ts` setup).
- **Side effects**: Changes to the `.md:hidden` utility classes or the `rounded-lg.border` container in the web app will break this test.

## External consumers

None known.
