---
node_id: concorda-test::pages/register.page.ts::RegisterPage.fillPersonalInfo
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 85d821df62b95bf3c1be169ece33c99d252c49c5262ba71186562668bfd39a89
status: llm_drafted
---

# RegisterPage.fillPersonalInfo

## Purpose

Automates the entry of user identity and credentials during the registration flow. It populates the personal information step of the registration wizard, handling both required and optional fields like phone and date of birth. Use this method after `selectMembershipByName` to advance the user from the membership selection step to the final account creation.

## Invariants

- **Input is a single object** containing `firstName`, `lastName`, `email`, and `password`.
- **`email` is doubled-entered** into both `emailInput` and `confirmEmailInput` to satisfy form validation.
- **`password` is doubled-entered** into both `passwordInput` and `confirmPasswordInput`.
- **`dateOfBirth` must follow `MM/DD/YYYY` format** to ensure the `isStepValid()` check passes and allows the user to proceed.

## Gotchas

- **`dateOfBirth` is a functional dependency for navigation.** Per the source comment, `handleNext` short-circuits via `isStepValid()` unless a valid `MM/DD/YYYY` date is provided. If the date is malformed, the "Next" button will remain disabled.
- **Selectors are sensitive to UI changes.** Commit `f552929` was required to align selectors with the actual UI to fix the first green run.
- **Avoid using placeholders for selection.** Commit `bee3134` changed the registration page to use `#id` selectors rather than placeholders to ensure stability.

## Cross-cutting concerns

- **Auth**: Part of the initial identity creation flow; successful completion leads to account creation.
- **Side effects**: Completion of this step (and subsequent registration) triggers the creation of a new user record in the database.

## External consumers

- `concorda-test::tests/auth/boat-owner-registration.spec.ts`
- `concorda-test::tests/boats/coowner-request.spec.ts`
