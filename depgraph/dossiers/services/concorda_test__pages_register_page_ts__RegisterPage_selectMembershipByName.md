---
node_id: concorda-test::pages/register.page.ts::RegisterPage.selectMembershipByName
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 665243556c28a878c5ee1c3a46913a59177231da65f691144b76fa2727c6550c
status: current
---

# RegisterPage.selectMembershipByName

## Purpose

Selects a specific membership tier (e.g., "Boat Owner" or "Mass Bay Sailor") by matching the provided string or regex against the radio button's accessible name. This method is used during the registration flow to transition from the membership selection step to the personal information step. Use this when a test needs to target a specific tier rather than just clicking the first available option.

## Invariants

- **Input is a `string | RegExp`** — the selector must match the `aria-label` or accessible name of the radio button.
- **Advances the state machine** — calling this method automatically triggers `this.nextButton.click()`, moving the user to the `fillPersonalInfo` step.
- **Requires a match** — if the provided name does not match an existing membership card, the Playwright locator will time out.

## Gotchas

- **Selector alignment** — per commit `030d6f9`, the method was updated to use the accessible name to ensure the selector matches the actual UI behavior.
- **Strict name matching** — per commit `f552929`, ensure the name passed matches the exact text rendered in the UI, as selectors were recently aligned to fix brittle test failures.

## Cross-cutting concerns

- **Auth**: Part of the registration flow; successful completion of this step (and subsequent `fillPersonalInfo`) is a prerequisite for creating a new authenticated user.
- **Side effects**: Successful completion of the full registration flow (which starts with this method) creates a new user record in the database.

## External consumers

- N/A — internal to `concorda-test`.
