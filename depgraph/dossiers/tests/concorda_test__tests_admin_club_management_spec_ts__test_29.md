---
node_id: concorda-test::tests/admin/club-management.spec.ts::test@29
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 97bdeb759043bf28b6023244216f50e97876266714c37edfa795414b7f3294ea
status: llm_drafted
---

# add club button opens dialog

## Purpose

Verifies the UI flow for adding a new club via the administrative dashboard. It ensures the "Add Club" dialog triggers correctly, handles optional fields (like email), and that the newly created entity is immediately searchable and visible in the club list.

## Invariants

- **Dialog visibility**: The `dialogNameInput` must be visible within a 3,000ms timeout after clicking the add button.
- **Searchability**: A new club must be discoverable via the `searchFor` method after the creation flow completes.
- **Input handling**: The test must account for the conditional visibility of `dialogEmailInput` to avoid hanging on unexpected UI states.

## Gotchas

- **Race conditions**: The test relies heavily on `page.waitForTimeout(1000)` and `page.waitForTimeout(2000)` to allow the UI to settle after clicks and form submissions. Removing these without replacing them with robust `waitForSelector` or `waitForResponse` calls will likely cause flaky failures in the CI environment.
- **Initial scaffolding**: Per commit `fd0c570`, this test is part of the initial Playwright E2E scaffolding; it is highly sensitive to changes in the `clubsPage` fixture structure.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (inherited from the `club-management.spec.ts` setup).
- **Side effects**: Creates a new club record in the database; ensure the test environment is reset or that the `E2E Test Yacht Club` name is unique to avoid collisions in shared environments.

## External consumers

None known.
