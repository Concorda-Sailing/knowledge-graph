---
node_id: concorda-test::tests/admin/user-management.spec.ts::test@41
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7a811b52bfe90bbb9674b520e65c518ef933e2fe7cc2938c0447373c1e933f09
status: current
---

# can create a new user

## Purpose

Verifies the end-to-end flow of creating a new user via the Admin dashboard. It ensures that the user creation dialog correctly accepts input and that the newly created user is immediately searchable and visible in the user list.

## Invariants

- **Requires unique email addresses** — Uses a timestamped `uniqueEmail` to prevent collisions with existing test users.
- **Uses `usersPage.addUserButton`** — The entry point for the creation flow must trigger the visibility of the dialog.
- **Search-based verification** — Verification is performed by calling `usersPage.searchFor(uniqueEmail)` rather than relying on list order.
- **Dialog field presence** — The test expects `dialogEmailInput`, `dialogPasswordInput`, `dialogFirstNameInput`, and `dialogLastNameInput` to be visible and interactable.

## Gotchas

- **Search dependency** — Per commit `dad4d2e`, the test must explicitly search for 'alice' (or the specific user) before performing subsequent admin actions to ensure the UI state is correctly positioned.
- **Selector fragility** — Per commit `f552929`, the UI selectors (specifically for the dialog and action buttons) frequently require alignment with the actual DOM to prevent test failures during green runs.
- **Implicit waits** — The test relies on `page.waitForTimeout` (e.g., 1000ms or 2000ms) to handle asynchronous UI transitions; removing these without replacing them with robust `waitForSelector` calls will likely cause flakiness in the dialog-opening steps.

## Cross-cutting concerns

- **Auth**: Requires an authenticated Admin session (likely established via `ApiClient.login` in the global setup).
- **Side effects**: Creates a new user record in the database; if run against a persistent environment, this increases the user count and may affect the `usersPage` list length.

## External consumers

None known.
