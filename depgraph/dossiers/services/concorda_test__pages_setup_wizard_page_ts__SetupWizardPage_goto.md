---
node_id: concorda-test::pages/setup-wizard.page.ts::SetupWizardPage.goto
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7210ac1f968a66967d77a3ec9ed2924182d4dc13e0b6218974aa26fcfc68ff97
status: current
---

# SetupWizardPage.goto

## Purpose

Navigates the user to the `/members/setup` route and handles the conditional onboarding gate. This method is essential for E2E tests that require a user to complete their profile (e.g., crew signup flows) before proceeding to features that depend on a completed sailing resume. It differentiates itself from a simple `page.goto` by managing the race between the "sailing experience" gate and the actual form hydration.

## Invariants

- **Navigates to `/members/setup`**.
- **Handles the "Yes, Let's Go" gate.** If the gate appears, the method clicks the button to reveal the form.
- **Uses a race condition for stability.** It waits for either the `yesButton` or the `aboutMeInput` to become visible to avoid timing issues with React hydration.
- **Requires a 15s timeout.** Both the gate and the form inputs have a 15,000ms window to ensure the test doesn't fail prematurely during slow environment boot-ups.

## Gotchas

- **The "sailing-question" gate is a race condition.** Per commit `cd62e08`, the method must race the `yesButton` against the `aboutMeInput` to prevent the test from hanging if the gate is skipped or if the form renders instantly.
- **The gate is not a simple visibility check.** It requires a regex match for the button text (`/yes, let.s go/i`) because of the specific punctuation in the UI.
- **Auto-save is a network-dependent event.** When using `fillSailingResume`, the method relies on `waitForAutoSave` to intercept a `PUT` request to `/profile/sailing-resume`. If the API endpoint changes or the request method is not `PUT`, the test will time out.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session; the `/members/setup` route is protected.
- **Side effects**: Completing this flow is a prerequisite for the `crew-signup-flow.spec.ts` to successfully reach the "publish" stage.

## External consumers

- `concorda-test::tests/auth/crew-signup-flow.spec.ts` (via `hook_call`)
