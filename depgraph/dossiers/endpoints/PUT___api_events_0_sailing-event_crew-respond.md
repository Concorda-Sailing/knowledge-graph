---
node_id: PUT::/api/events/{0}/sailing-event/crew-respond
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4b2fc2de75c1f5a9b0dd221c96c9750cd39aa9fe21446e1f1ee3acbbff0bdcbc
status: current
---

# PUT /api/events/{event_id}/sailing-event/crew-respond

## Purpose

Allows a user to accept or decline an invitation to join a sailing event's crew. This endpoint is distinct from general event updates as it specifically manages the transition of an `EventCrew` record from `invited` to `accepted` or `declined`. When a user accepts, the logic handles position validation (ensuring the slot isn't already full) and automatically updates the user's `SailingResume` to include the new position.

## Invariants

- **Method/Path**: `PUT /api/events/{event_id}/sailing-event/crew-respond`.
- **Auth**: Requires a valid session via `require_auth`; the user must be a member of the crew (verified via `_get_user_sailing_event_or_404`) to respond.
- **Action Constraint**: The `data.action` must be exactly `"accept"` or `"decline"`.
- **Position Validation**: If `action == "accept"`, the `position_name` must exist within the event's `positions_needed` and the current `taken_count` must be less than `pos_count`.
- **Return Shape**: Returns the updated `EventCrewRead` object.

## Gotchas

- **Side effect on `SailingResume`**: Accepting a position mutates the user's `SailingResume.positions_preferred` list. This is a critical side effect for users tracking their experience.
- **Roster Re-evaluation**: Calling `decline` triggers `evaluate_roster` (from `services.crew_roster`), which may promote alternates.
- **Race conditions on positions**: The check for `taken_count >= pos_count` happens in-memory during the request; high-concurrency environments might see over-subscription if multiple users accept simultaneously.
- **Commit/Broadcast Order**: The function calls `db.commit()` after `evaluate_roster` but before `broadcast_event`. If the broadcast fails, the DB change is already permanent.

## Cross-cutting concerns

- **Auth**: Guarded by `require_auth`.
- **Websocket**: Emits `EVENT_CREW_UPDATED` via `broadcast_event` to notify active listeners of the change.
- **Side effects**: Triggers `evaluate_roster` on decline; updates `SailingResume` on acceptance.
- **Audit**: N/A.

## External consumers

- `concorda-web` (via `eventsApi.respondToEventCrew`)
- `concorda-test` (via `ApiClient.respondToEventCrewInvite`)

## Open questions

- Should the `SailingResume` update be moved to a background task or a dedicated service to ensure the API response time remains low if the resume object grows significantly?
