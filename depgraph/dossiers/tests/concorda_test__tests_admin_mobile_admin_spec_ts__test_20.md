---
node_id: concorda-test::tests/admin/mobile-admin.spec.ts::test@20
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0e3660fb9984812775fc09071ce826a224b9a214b7377629538b63f068e3c092
status: current
---

# admin dialog fits within viewport when opened

## Purpose

Verifies that the Admin User management interface is mobile-responsive. Specifically, it ensures that the "Add User" dialog fits within a standard mobile viewport width and that the page does not produce horizontal overflow. This test is distinct from the desktop regression tests in the same file, which explicitly set a larger viewport to ensure the desktop table remains visible.

## Invariants

- **Viewport width constraint**: The "Add User" dialog must have a bounding box width less than or equal to 369px (`375 - 16` padding/margin).
- **No horizontal overflow**: The document `scrollWidth` must not exceed 376px to prevent side-scrolling on mobile devices.
- **Data loading dependency**: The test must wait for the user list to load (via heading visibility and card/border visibility) before interacting with the "Add User" button to avoid race conditions.

## Gotchas

- **Race conditions on data load**: Recent commit `02bd90c` added explicit waits for data loading (checking for the user heading and the `.md\:hidden` card border) before clicking the "Add User" button. Without these waits, the test fails because the button is not yet interactive or visible.
- **Desktop regression requirement**: Per commit `625d101`, a separate `test.describe` block is required to ensure that mobile-specific CSS (like `md:hidden` classes) does not accidentally hide the desktop table for users on larger screens.

## Cross-cutting concerns

- **Auth**: Requires authenticated admin access to reach `/members/admin/users`.
- **Side effects**: Changes to the layout of the `AdminListPage` or the `Add User` dialog component will directly impact this test's success.

## External consumers

None known.
