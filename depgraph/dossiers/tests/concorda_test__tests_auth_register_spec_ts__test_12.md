---
node_id: concorda-test::tests/auth/register.spec.ts::test@12
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 53d4a9ebb12370c4b48aa905a9dddfcfdbdcce2705045beb8870a5652b0f8753
status: llm_drafted
---

# registration page loads with membership options

## Purpose

Verifies that the registration page correctly loads membership options and handles the end-to-end flow for a free membership signup. This test ensures that users can navigate through personal info, preferences, and legal policy acceptance to reach the email verification stage. It is distinct from the login tests as it validates the creation of new identities rather than the authentication of existing ones.

## Invariants

- **Membership selection is required.** The test must first call `registerPage.selectFreeMembership()` to initialize the flow.
- **Registration is gated by legal policies.** The user must interact with all visible checkboxes (TOS, Privacy, etc.) to enable the "Complete Registration" button.
- **Success state is an email-verification panel.** For free and uninvited signups, the final view is a "Check your e-mail" heading rather than a dashboard redirect.
- **Email/Sign-in copy is flexible.** The test uses regex to match both "Sign in" and "Go to login" to account for minor UI copy changes.

## Gotchas

- **Policy checkbox count is dynamic.** Per the code comment, the registration form gates "Complete" on every active policy. If a fourth policy (e.g., a waiver) is added, the loop `for (let i = 0; i < n; i++)` ensures the test doesn't fail by skipping the new checkbox.
- **Email verification landing page.** Per commit `98d9ace`, free signups land on an email-verification panel. Tests must assert on the "check your e-?mail" heading and the subsequent "sign in" link rather than expecting a direct dashboard redirect.
- **Regex-based button matching.** The "Complete Registration" button is matched via a case-insensitive regex (`/^complete registration$/i`) to avoid brittle failures on casing changes.

## Cross-cutting concerns

- **Auth**: Triggers the creation of a new user identity; success depends on `auth.py` setting `needs_verification = is_free`.
- **Side effects**: Creates a new user in the database, which may affect downstream user-count metrics or dashboard statistics.

## External consumers

None known.
