---
node_id: concorda-test::pages/setup-wizard.page.ts::SetupWizardPage.waitForAutoSave
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 61a1676dc8d68c0dbeb14af53dc60f0abe362ff5bebbcce68d4383cb2094550a
status: current
---

# SetupWizardPage.waitForAutoSave

## Purpose

Waits for the asynchronous auto-save operation to complete after a user mutation in the Setup Wizard. It specifically listens for a `PUT` request to the `/profile/sailing-resume` endpoint. Use this method instead of manual timeouts to ensure the backend has successfully processed changes before the test proceeds to the next step of the onboarding flow.

## Invariants

- **Target endpoint is `/profile/sailing-resume`**.
- **HTTP method must be `PUT`**.
- **Timeout is hardcoded to 10,000ms**.
- **Triggered by mutations** to the sailing resume fields (e.g., `aboutMe`, `experience`, `yearsSailing`).

## Gotchas

- **Race conditions with the "sailing-question" gate**: Recent work in commit `cd62e08` shows that the sailing-question gate can race against the resume form. Ensure `waitForAutoSave()` is called to prevent the test from proceeding to the next step before the profile update is persisted, which can cause the gate to fail or behave inconsistently.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to successfully perform the `PUT` request.
- **Side effects**: Successful completion of this method is a prerequisite for advancing through the onboarding wizard steps (e.g., moving from the resume stage to the sailing-question gate).

## External consumers

None known.
