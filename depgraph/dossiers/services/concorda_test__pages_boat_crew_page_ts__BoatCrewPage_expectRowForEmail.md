---
node_id: concorda-test::pages/boat-crew.page.ts::BoatCrewPage.expectRowForEmail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c29556c160a9a85e7e45a8798786f842786a387c298a89542d06d7c888b564a6
status: current
---

# BoatCrewPage.expectRowForEmail

## Purpose

Provides a specialized assertion for verifying the presence of a crew member in the Boat Crew tab. It is used to confirm that an invited or active crew member is visible with a specific status/role badge. Use `expectRowForEmail` when testing flows involving email-based invitations, and `expectRowForName` when the user is already a known member of the organization.

## Invariants

- **Requires a visible element.** The method asserts that a `div`, `li`, or `tr` containing the target text is visible within a 10,000ms timeout.
- **Status matching is flexible.** The `status` argument accepts a `string` or a `RegExp` to allow for partial matches of role badges (e.g., "Active" or `/Active/i`).
- **Email lookup is fallback-heavy.** If the target is an external email with no existing account, the method will fail because no DOM element exists for that identity.

## Gotchas

- **External emails have no DOM presence.** Per the docstring, if the invite target is an external email with no existing account, there is no visible card; callers must verify via API/email capture instead of this method.
- **Locator noise.** The `crewContainer` locator can be noisy when multiple boats are on-screen, so this method uses a broad `div, li, tr` filter to find the email/name fragment.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the Boat Crew tab.
- **Side effects**: Verifies the visibility of rows in the boat-crew-tab UI.

## External consumers

None known.
