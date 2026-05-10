---
node_id: concorda-test::pages/setup-wizard.page.ts::SetupWizardPage.fillSailingResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a9924d3937eb5fc9df0ef5d10b033cb2f976dc69533d58cdc53eed307fa3b890
status: current
---

# SetupWizardPage.fillSailingResume

## Purpose

Automates the population of the user's sailing resume during the onboarding wizard. It handles the mandatory `aboutMe` and `experience` fields while optionally filling out experience-specific details like `yearsSailing` and `positions`. Use this method when a test needs to move a user past the initial profile setup to a completed state.

## Invariants

- **Requires `aboutMe` (string) and `experience` (string label).** These are the minimum fields required by the UI to proceed.
- **`experience` must be a valid option label.** Passing an arbitrary string that doesn't match the select options (e.g., "Intermediate") will cause the selector to fail.
- **`yearsSailing` is cast to a string.** The method converts the numeric input to a string before calling `.fill()`.
- **Ends with `waitForAutoSave()`.** This ensures the asynchronous background save completes before the test proceeds to the next step of the wizard.

## Gotchas

- **Race conditions with the "sailing-question" gate.** Per commit `cd62e08`, this method must be used in conjunction with logic that handles the sailing-question gate to avoid timing issues where the form is not yet interactive or is interrupted by a modal.
- **Order of operations matters for the wizard flow.** Recent history (commits `cd62e08` and `9f6450e`) indicates that the "sailing-question" gate (e.g., "Yes, Let's Go") must be handled to ensure the resume form is actually reachable and stable.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Completing this step is a prerequisite for the `crew-signup-flow` to reach the "publish" stage.

## External consumers

- `concorda-test::tests/auth/crew-signup-flow.spec.ts` (used in the crew signup E2E flow).
