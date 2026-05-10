---
node_id: concorda-test::tests/auth/register.spec.ts::test@76
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2788cf463d50aaf0a44f372429aef8bd43716f4ebb1a931d8daf1a1b416352ce
status: llm_drafted
---

# duplicate email shows error and blocks progression

## Purpose

Verifies the error handling and validation logic during the registration flow. Specifically, it ensures that the registration process is blocked when a user attempts to use an existing email address or a password that fails complexity requirements. This test is critical for ensuring that the `authApi.checkEmail` availability check correctly prevents unauthorized progression to the next step of the onboarding funnel.

## Invariants

- **Email uniqueness is enforced via `authApi.checkEmail`** — the UI must surface the "already registered" error before allowing the user to advance.
- **Progression is blocked on validation failure** — the "Personal Information" section (rendered as a `div` via shadcn/ui) must remain visible to prove the user did not advance past the current step.
- **Password validation is real-time** — the `nextButton` must be in a `disabled` state if the password does not meet the minimum length and complexity requirements.
- **Error state is cleared on input change** — modifying the `emailInput` must trigger a reset of the `emailTaken` state to allow for successful progression.

## Gotchas

- **UI copy sensitivity** — commit `9965eb9` highlights that changes to UI text (e.g., "Sign in" vs "Go to login") frequently break these specs; assertions on text like "this email is already registered" must be maintained if the API response or UI copy is updated.
- **Non-heading element detection** — the "Personal Information" card title is a `div`, not a `heading`, which requires specific selection logic to verify that the user is still on the current step during a blocked progression.

## Cross-cutting concerns

- **Auth**: Directly tests the failure modes of the registration/onboarding flow.
- **Side effects**: Prevents the creation of duplicate user accounts in the test database.

## External consumers

None known.
