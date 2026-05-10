---
node_id: concorda-test::tests/admin/club-management.spec.ts::test@36
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5e0859741348b9364b1acc74ab5e6c214fca2de61eee652cb03b9c8202af24bf
status: llm_drafted
---

# can create a new club

## Purpose

Verifies the end-to-end lifecycle of club creation and editing within the Admin dashboard. It ensures that the "Add Club" flow correctly triggers the modal, handles optional fields (like email), and that newly created entities appear in the searchable list.

## Invariants

- **Modal visibility**: The `dialogNameInput` must be visible before any interaction with form fields can occur.
- **Searchability**: A successful creation must result in the new club name being visible in the `clubsPage.searchFor` results.
- **Conditional fields**: The `dialogEmailInput` is treated as an optional field; the test must check for its visibility before attempting to fill it.

## Gotchas

- **Implicit delays**: The test relies on `page.waitForTimeout(1000)` and `page.waitForTimeout(2000)` to handle UI transitions and API latency. Removing these or replacing them with more robust `waitForSelector` calls may be necessary if the test becomes flaky in CI.
- **Search-based verification**: The test uses `page.getByText(/e2e test yacht club/i)` to verify creation. If the search implementation in `clubsPage.searchFor` is not working, this test will fail even if the record was successfully created in the backend.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `ApiClient.login` or a pre-existing `storageState`) to access the Admin dashboard.
- **Side effects**: Successful execution creates a new club record in the database; ensure the test environment is reset or uses unique names to avoid collision-based failures.

## External consumers

None known.
