---
node_id: concorda-test::tests/admin/user-management.spec.ts::test@33
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f47a06beefd3e8df186d6ae47b7b3c85dfe444713f91a58e054cd427969d6bc8
status: llm_drafted
---

# add user button opens dialog

## Purpose

Verifies that the "Add User" dialog correctly initializes and submits user creation data. This test ensures that clicking the add button reveals the necessary input fields (email, password, first name, last name) and that the resulting user is successfully persisted and searchable in the user list.

## Invariants

- **Dialog visibility**: The `dialogEmailInput` must be visible within a 3,000ms timeout after clicking the add button.
- **Data persistence**: A new user created via the dialog must be searchable by their unique email address immediately after the save operation.
- **Input requirements**: The dialog must provide distinct fields for `email`, `password`, `firstName`, and `lastName`.

## Gotchas

- **Selector alignment**: Recent changes in `f552929` were required to align selectors with the actual UI to ensure the first green run.
- **Search dependency**: Per commit `dad4d2e`, the test must explicitly search for a known user (e.g., 'alice') before attempting to interact with or assert on existing user rows to ensure the UI state is stable.
- **Race conditions**: The test relies on `page.waitForTimeout(1000)` and `page.waitForTimeout(2000)` to allow for dialog animations and API latency; removing these without replacing them with robust `expect` assertions will cause flakiness.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (established via `ApiClient.login` in the global setup) to access the user management dashboard.
- **Side effects**: Successful creation via this test adds a record to the user database, which may affect user count displays in other admin views.

## External consumers

None known.
