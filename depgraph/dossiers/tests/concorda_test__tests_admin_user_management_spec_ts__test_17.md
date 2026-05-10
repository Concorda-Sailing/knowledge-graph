---
node_id: concorda-test::tests/admin/user-management.spec.ts::test@17
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c04e727924e56fab354c538b305d754bf85129061cfb0506470ec5761f440555
status: current
---

# shows seeded users in table

## Purpose

Verifies that seeded users are correctly visible and searchable within the Admin User Management table. This test ensures that the user list correctly renders existing members (like the "Alice" seed) and that the search functionality correctly filters the view.

## Invariants

- **Table sorting is by last name.** The test relies on the fact that the "Alice" user may not be on the first page of a large dataset.
- **Search is required for visibility.** Because the production-sized seed contains ~635 rows, the test must use `usersPage.searchFor()` to bring the target user into the viewport.
- **`usersPage.userTable` must be visible** with a 10s timeout before any interaction occurs.

## Gotchas

- **Large seed volume.** Per commit `dad4d2e`, the test must explicitly search for "alice" before asserting her row is visible, as she is not on page 1 in a 635-row production-sized seed.
- **Selector alignment.** Per commit `f552929`, selectors must be carefully aligned with the actual UI to prevent failures during the initial green run.

## Cross-cutting concerns

- **Auth**: Requires an authenticated Admin session (established via `AdminUsersPage` setup).
- **Side effects**: Creating a new user via the `addUserButton` flow creates a persistent record in the test database.

## External consumers

None known.
