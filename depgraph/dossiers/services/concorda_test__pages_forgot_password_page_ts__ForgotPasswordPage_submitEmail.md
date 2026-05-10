---
node_id: concorda-test::pages/forgot-password.page.ts::ForgotPasswordPage.submitEmail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 52c97bd61c561082bcb3c0261ddfea48c482b3ad33c0b0572f21bf552552d12d
status: llm_drafted
---

# ForgotPasswordPage.submitEmail

## Purpose

The `submitEmail` method triggers the password reset request flow by filling the email input and clicking the submit button. It is used in E2E tests to verify that the system correctly handles the "forgot password" lifecycle, specifically checking that the UI transitions to the success message state.

## Invariants

- **Input is a raw email string.** The method expects a string that matches the expected email format for the user-facing input.
- **Click triggers the success state.** After execution, the test should assert against `this.successMessage` to confirm the request was processed.
- **Uses regex-based selectors.** The `submitButton` and `successMessage` rely on loose text matching (`/send|reset|submit/i` and `/if an account exists/i`) to remain resilient to minor UI text changes.

## Gotchas

- **Initial scaffolding state.** Per commit `fd0c570`, this is part of the initial E2E suite scaffolding; the page object structure is currently minimal and may require updates as the actual `/forgot-password` route implementation matures.

## Cross-cutting concerns

- **Auth**: none (this is a pre-authentication flow).
- **Side effects**: Triggers the backend password reset email/flow, which may impact user account state in the test environment.

## External consumers

None known.
