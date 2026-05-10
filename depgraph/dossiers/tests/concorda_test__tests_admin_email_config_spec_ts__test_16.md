---
node_id: concorda-test::tests/admin/email-config.spec.ts::test@16
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 45f38d0390f592fd96c7f8b5b30e995720e78b85bbec57c7e9de99115340399e
status: llm_drafted
---

# email settings section is accessible

## Purpose

Verifies that the Email Settings section of the Admin dashboard is accessible and correctly renders configuration elements. This test ensures that the `/members/admin/email` route is reachable and that the UI displays the expected "Email Settings" and "Send Test Email" sections.

## Invariants

- **URL path must be `/members/admin/email`**.
- **Page must reach `networkidle` state** before asserting on visibility to ensure the configuration-heavy UI has loaded.
- **UI must contain specific keywords** (`email settings`, `email mode`, or `smtp`) to pass, as the page relies on dynamic text for element identification.

## Gotchas

- **Selectors are brittle and require frequent alignment with the UI.** Commit `f552929` was specifically required to "align selectors with actual UI" to fix the setup for the first green run.
- **Implicit timeouts are necessary.** The test uses explicit timeouts (e.g., `10_000` and `5_000`) for visibility checks to account for the loading state of the admin configuration components.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session (implicitly handled by the test setup/systemPage).
- **Side effects**: Verifying the "Save" button visibility (line 36) ensures the configuration form is interactive.

## External consumers

None known.
