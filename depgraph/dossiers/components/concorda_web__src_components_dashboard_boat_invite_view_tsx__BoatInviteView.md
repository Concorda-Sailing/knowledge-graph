---
node_id: concorda-web::src/components/dashboard/boat-invite-view.tsx::BoatInviteView
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 11571ea7126911292806d36c3ab05a6bf26a42c900e71eb43f2b1872f599fbbe
status: current
---

# BoatInviteView

## Purpose

Renders the detailed view of a boat invitation, allowing a user to view boat details (name, sail number, picture) and respond to the invite. It orchestrates three concurrent API calls via `boatApi` to fetch the boat's full profile, resume, and crew list to ensure the UI is populated with real-time data before the user makes a decision.

## Invariants

- **Fetches three distinct resources** via `boatApi.getDetail`, `boatApi.getResume`, and `getCrew` using the `invitation.boat_uuid`.
- **Uses `Promise.allSettled`** to ensure that a failure in one resource (e.g., a missing crew list) does not prevent the boat's basic identity (name/sail number) from rendering.
- **Requires an `onRespond` callback** to handle state transitions after the user interacts with the invitation.
- **Displays a fallback identity** using `invitation.boat_name` or `invitation.boat_sail_number` if the fetched `boat` object is null or incomplete.

## Gotchas

- **Race condition on response**: The `setTimeout` of 1500ms after a successful "accept" action is used to allow the `toast` to remain visible to the user before the `onRespond` callback triggers a navigation or view change.
- **Data fallback logic**: The component relies on a specific hierarchy for identity: `boat.name` -> `invitation.boat_name` -> `invitation.boat_sail_number`. If the API returns a partial object, the UI must not break.

## Cross-cutting concerns

- **Auth**: Depends on `boatApi` which requires an authenticated session to access boat-specific details and crew lists.
- **Side effects**: Successful "accept" action triggers `onRespond()`, which typically refreshes the dashboard view or navigates the user away from the invitation state.

## External consumers

None known.

## Open questions

- Should the `onRespond` delay (1500ms) be configurable or moved to a global constant to ensure consistency across all invitation-type components?
