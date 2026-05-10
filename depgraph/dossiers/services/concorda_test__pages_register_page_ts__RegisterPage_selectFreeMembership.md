---
node_id: concorda-test::pages/register.page.ts::RegisterPage.selectFreeMembership
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 581065548bdff4c6a4829064f50b52e682b6000dffadea76e10870d97b4153b9
status: current
---

# RegisterPage.selectFreeMembership

## Purpose

The `selectFreeMembership` method automates the selection of the default free tier during the registration flow. It is a specialized, high-level helper used to bypass the membership selection step by clicking the first available card (the "Mass Bay Sailor" tier) and advancing to the personal information step. Use this instead of `selectMembershipByName` when the test intent is simply to create a user without needing to verify specific tier-based access or pricing.

## Invariants

- **Clicks the first element** in the `membershipCards` collection.
- **Automatically advances the flow** by calling `this.nextButton.click()` immediately after selection.
- **Requires the registration page to be loaded** via `goto()` before invocation.

## Gotchas

- **Selector fragility:** Recent changes in `f552929` indicate that the registration UI selectors are highly sensitive to changes in the component structure.
- **Accessibility dependency:** As seen in commit `030d6f9`, the registration flow relies on specific accessible names and roles; if the "free" tier is no longer the first element or its role changes, this method will fail to select the intended tier.

## Cross-cutting concerns

- **Auth**: This is a pre-authentication step used to create the user identity that is later used in authenticated flows.
- **Side effects**: Successful completion of the flow initiated by this method results in a new user record in the database, which is a prerequisite for tests involving `coowner-request.spec.ts`.

## External consumers

- `concorda-test::tests/boats/coowner-request.spec.ts` (via hook call)
