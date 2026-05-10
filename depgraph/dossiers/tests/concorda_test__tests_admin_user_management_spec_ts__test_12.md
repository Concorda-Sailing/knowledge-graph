---
node_id: concorda-test::tests/admin/user-management.spec.ts::test@12
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 728f90bdb10bd1225fe825f4c0204fbc7d8b57b668a5372365f892911d09193e
status: current
---

# user list page loads

## Purpose

Verifies that the Admin User Management page loads correctly and that the user table is visible. This serves as the baseline smoke test for the admin user dashboard, ensuring the `AdminUsersPage` fixture and the underlying routing for `/members/admin/users` are functional before more complex CRUD tests execute.

## Invariants

- **URL pattern**: The page must match the regex `/\/members\/admin\/users/`.
- **Visibility**: The `userTable` must be visible within a 10,000ms timeout.
- **Page Object**: Relies on `AdminUsersPage` to encapsulate the `page` and `userTable` selector.

## Gotchas

- **Large seed sets**: As noted in commit `dad4d2e`, the test must account for a production-sized seed (~635 rows). While this specific test only checks visibility, subsequent tests in this file (like `shows seeded users in table`) require searching for users like "alice" because they will not appear on the first page of a large dataset.
- **Selector fragility**: Recent work in `f552929` was required to align selectors with the actual UI; ensure any changes to the `AdminUsersPage` class do not break the `userTable` visibility check.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (handled by the `AdminUsersPage` setup/navigation).
- **Side effects**: Verifies the entry point for user-related administrative actions (Create, Edit, Search).

## External consumers

None known.
