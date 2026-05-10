---
node_id: concorda-test::tests/auth/register.spec.ts::test@19
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3dcdf0ef225b078898a79b323e575fb20dd40635ab83a3034415a951574fcbc7
status: llm_drafted
---

# full free membership registration flow

## Purpose

Validates the end-to-end flow for a user registering with a "Free" membership tier. It ensures that the registration process correctly handles personal info, navigates through the policy/preference steps, and lands the user on the email verification success panel rather than the dashboard.

## Invariants

- **Requires email verification.** Unlike invited users, free signups must land on a panel with "check your e-mail to verify" or "check your e-mail" text.
- **Must interact with all active policies.** The test iterates through all visible checkboxes (TOS, Privacy, etc.) to ensure the "Complete Registration" button is enabled.
- **Uses unique email generation.** Uses `test.reg.${Date.now()}@test.concorda` to prevent collisions during parallel test runs.
- **Regex-based CTA matching.** The final step requires matching the "Complete Registration" button via a case-insensitive regex to avoid brittle string-matching failures.

## Gotchas

- **Policy checkbox dependency.** The registration form gates the "Complete" button on the active status of all policies. If a new policy (e.g., a waiver) is added, the loop in the test must successfully click it, or the test will hang/fail at the final step.
- **Email/E-mail spelling variance.** Per commit `98d9ace`, the success panel text can vary between "email" and "e-mail"; the test uses a regex `/check your e-?mail/i` to handle this.
- **Success panel landing.** Per commit `98d9ace`, free signups land on an email-verification panel rather than the dashboard. Assertions must look for the "sign in" or "go to login" link to confirm the flow completed.

## Cross-cutting concerns

- **Auth**: Triggers `auth.py` logic where `needs_verification` is set to `true` for free/uninvited users.
- **Side effects**: Successful completion triggers the creation of a new user record in the test database.

## External consumers

None known.
