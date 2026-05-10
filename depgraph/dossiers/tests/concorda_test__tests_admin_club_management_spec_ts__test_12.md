---
node_id: concorda-test::tests/admin/club-management.spec.ts::test@12
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8ad991408f523251aea9fd36ade32a34b5435faa09737894903e2d3dbccd2d14
status: llm_drafted
---

# clubs page loads with seeded organizations

## Purpose

Verifies the administrative lifecycle of "Clubs" within the admin dashboard. It ensures that the club list loads with seeded data, search filters function correctly, and that the creation/edit dialogs (including optional fields) are operational. This test is a core part of the admin E2E suite, ensuring that the central organizational unit of the platform remains manageable.

## Invariants

- **Requires `AdminClubsPage` fixture.** The test relies on the `AdminClubsPage` class to abstract the selector logic for the club table and dialogs.
- **Relies on seeded data.** The test expects the presence of approximately 50 seeded yacht clubs to pass the initial visibility and count assertions.
- **Search is asynchronous.** The `searchFor` method and subsequent row counts require explicit `page.waitForTimeout` or visibility checks because the UI does not immediately update.
- **Dialog field optionality.** The `dialogEmailInput` is treated as optional in the creation flow; the test must check visibility before attempting to fill it to avoid failure.

## Gotchas

- **Implicit race conditions.** The test uses multiple `page.waitForTimeout(1000)` and `page.waitForTimeout(2000)` calls to account for the asynchronous nature of the React state updates after clicking "Save" or "Search". Removing these without replacing them with robust `waitForSelector` or `waitForResponse` calls will lead to flaky failures in the CI environment.
- **Initial commit scaffolding.** Per commit `fd0c570`, this suite is part of the initial E2E scaffolding; it is currently highly dependent on the stability of the `AdminClubsPage` object model.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (typically established via `api.login` in a global setup or a higher-level `beforeEach`).
- **Side effects**: Creating a club via `dialogSaveButton.click()` persists a new record to the database, which may affect subsequent runs if the test suite is not running against a fresh/reset database instance.

## External consumers

None known.
