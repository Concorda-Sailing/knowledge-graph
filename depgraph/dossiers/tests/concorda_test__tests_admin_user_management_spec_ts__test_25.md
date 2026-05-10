---
node_id: concorda-test::tests/admin/user-management.spec.ts::test@25
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3e7afd60eaffbaa430e90f9f9a2a56635e6a85edafb9fce33b9cb0383d8c72f9
status: llm_drafted
---

# search filters users

## Purpose

Verifies the user search functionality within the Admin User Management interface. It ensures that the search input correctly filters the user table, allowing an administrator to locate specific users (like the seeded "Alice") amidst a large dataset.

## Invariants

- **Search is required for large datasets.** Because the production-sized seed contains ~635 rows, the table is sorted by last name and users like "Alice" may not appear on page 1 without a search.
- **Search results must be visible.** The test expects the filtered row to be visible within a 5,000ms timeout after the search is executed.
- **Input is case-insensitive.** The test uses a regex `/alice/i` to assert visibility, implying the UI handles case-insensitive matching.

## Gotchas

- **Large seed volume requires explicit search.** Per commit `dad4d2e`, the test must call `usersPage.searchFor('alice')` before asserting her row is visible, as she is not on page 1 of the 635-row prod-sized seed.
- **UI/Selector misalignment.** Per commit `f552929`, selectors and setup must be carefully aligned with the actual UI to ensure the first green run passes.

## Cross-cutting concerns

- **Auth**: Requires an authenticated Admin session (likely established via `ApiClient.login` in the global setup).
- **Side effects**: Successful user creation or editing in related tests may change the state of the user table, but this specific test relies on a stable seeded user ("Alice").

## External consumers

None known.
