---
node_id: concorda-test::pages/boat-crew.page.ts::BoatCrewPage.openBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1e869b928a588d4f3d063eebb41bec1f049800db72cf0c8b6bceb64573313c96
status: current
---

# BoatCrewPage.openBoat

## Purpose

Navigates the Playwright browser to the "My Crew" tab within the members page. It serves as a high-level Page Object Model (POM) helper to ensure the UI is in the correct state before testing crew-related actions (inviting, viewing, or managing members). It is distinct from `openCrewTab` in that it handles the initial navigation to `/members?tab=crew` and includes logic to handle deep-link failures.

## Invariants

- **Navigates to `/members?tab=crew`** — the primary entry point for the crew view.
- **Ensures `myCrewTab` is selected** — if the tab is visible but not currently active (e.g., due to a deep-link failure or slow paint), the method explicitly clicks it.
- **Uses `networkidle`** — waits for the network to be idle after navigation and after clicking the tab to ensure the crew list has loaded.
- **`_boatName` is a placeholder** — the argument is kept for API compatibility with Task-8 starter templates but is not used for actual routing logic.

## Gotchas

- **Deep-link fragility** — if the user is not yet a boat owner when the page first paints, the `myCrewTab` might not be visible or selected immediately. The method includes a `catch(() => false)` on the visibility check to prevent the test from crashing if the tab is temporarily detached from the DOM during a state transition.
- **Row lookup ambiguity** — per the docstring in `expectRowForEmail`, the `crewContainer` locator can be "noisy" when multiple boats are on-screen. Callers should be aware that searching for a row via email might require a fallback to page-wide searches if the specific container is unstable.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session (likely via `ApiClient.login` or a similar setup) as the `/members` route is protected.
- **Side effects**: Navigating here and interacting with the crew UI (via `inviteByEmail`) will trigger changes in the user's boat membership/crew list.

## External consumers

None known.
