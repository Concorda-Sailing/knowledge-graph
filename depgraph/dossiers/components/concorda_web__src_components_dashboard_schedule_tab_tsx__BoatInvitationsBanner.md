---
node_id: concorda-web::src/components/dashboard/schedule-tab.tsx::BoatInvitationsBanner
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8519b1a4cd30af52660b5a36a8ee93adb7c8be4b2922818c3ad5199bfa688f5d
status: llm_drafted
---

# BoatInvitationsBanner

## Purpose

Displays a high-priority banner for pending boat crew invitations on the Schedule tab. It provides a summary of the invitation (boat name/sail number and role) and allows the user to accept or decline the request via the `onRespond` callback. This component is used to surface actionable social-scheduling requests that require user interaction before they are integrated into the event roster.

## Invariants

- **`invitations` must be a non-empty array** to render; if the array is empty, the component returns `null`.
- **`onRespond` handles the side effect** of the user's choice; the component itself is stateless regarding the actual API call.
- **`respondingId` tracks active requests** to disable buttons and prevent double-clicking/multiple submissions for the same invitation.
- **`boatLabel` fallback logic** ensures a name is always visible; it prioritizes `boat_name`, then `boat_sail_number`, defaulting to `"a boat"` if neither exists.

## Gotchas

- **Mobile responsiveness/spacing:** Per commit `21f7cb5`, the banner requires tighter spacing and full-width actions on `<md` screens to ensure the "Accept" and "Decline" buttons remain usable on small devices.
- **Button disabling:** The `isBusy` state (driven by `respondingId`) is critical to prevent users from firing multiple requests if the network is slow.

## Cross-cutting concerns

- **Auth**: Relies on the user's authenticated session to process the `onRespond` action.
- **Side effects**: Successful responses via `onRespond` typically trigger a re-fetch of the schedule data, updating the `CrewRosterRow` and the overall event state.

## External consumers

None known.
