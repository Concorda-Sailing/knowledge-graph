---
node_id: concorda-test::pages/setup-wizard.page.ts::SetupWizardPage.selectExperience
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4f35940b99096ae7d219cc160c458b3a12049772b8ec3218d54318e86d6e513a
status: current
---

# SetupWizardPage.selectExperience

## Purpose

Interacts with the `experienceLevelSelect` dropdown in the Setup Wizard. It is used to select a specific experience level (e.g., "Beginner", "Intermediate") by its visible label. This is a specialized helper for the `fillSailingResume` flow, distinct from `togglePosition` which handles individual badge selection.

## Invariants

- **Input is a visible label string.** The `label` must match the text of an `<option>` element within the experience select component.
- **Requires an active session.** This method is called during the onboarding/setup flow, which follows the initial authentication steps.
- **Triggers a network side effect.** Selecting an option via this method is part of the stateful interaction that eventually triggers the `PUT /profile/sailing-resume` auto-save.

## Gotchas

- **Race conditions with the sailing-question gate.** Per commit `cd62e08`, this interaction must be carefully timed against the sailing-question gate to ensure the resume form is fully interactive before attempting to select an experience level.
- **Dependency on auto-save timing.** If using `fillSailingResume`, the test must account for the 1s delay and the subsequent `PUT` request to `/profile/sailing-resume` to avoid asserting against stale data.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session established via `LoginPage` or similar.
- **Side effects**: Updates the user's sailing profile, which is a prerequisite for completing the onboarding wizard.

## External consumers

None known.
