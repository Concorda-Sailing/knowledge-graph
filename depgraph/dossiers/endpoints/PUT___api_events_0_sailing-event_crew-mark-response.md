---
node_id: PUT::/api/events/{0}/sailing-event/crew-mark-response
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: dc5d1d1a3f8438620d144d02df052adde4f41a15b47271f45e360303eae59425
status: llm_drafted
---

# PUT /api/events/{event_id}/sailing-event/crew-mark-response

## Purpose

Allows an event owner (skipper) to manually update a crew member's status to either `accepted` or `declined`. This is used for crew members who have confirmed their attendance via out-of-band communication (e.g., text or phone) or for those who do not use the app, ensuring the digital roster remains accurate. It is distinct from the user-facing "accept/decline" flow where the crew member updates their own status.

## Invariants

- **Method/Path**: `PUT /{event_id}/sailing-event/crew-mark-response`.
- **Auth**: Requires `require_auth` and the user must be the `owner` of the sailing event (verified via `_get_user_sailing_event_or_404`).
- **Input**: `data.action` must be exactly `"accept"` or `"decline"`.
- **Status Constraint**: The target `EventCrew` record must currently be in the `"invited"` status; attempting to mark a non-invited status results in a 400 error.
- **Return Shape**: Returns an `EventCrewRead` object representing the updated record.

## Gotchas

- **Triggers Roster Re-evaluation**: If the action is `"decline"`, the system calls `evaluate_roster` (from `services.crew_roster`). This is a critical side effect that may affect downstream logic regarding event capacity or crew counts.
- **Notification Side Effects**: Per commit `8f84d2d feat(email): templated event_crew notifications + renderer hardening`, this endpoint triggers a specific email notification to the `crew_person`. The email is rendered using `render_event_crew_marked_response_email` to ensure the skipper's name and the event name are correctly formatted in the body.
- **Manual Overrides**: This endpoint is the primary way to fix "stale" or "out-of-sync" records when a user fails to interact with the app, as noted in the docstring.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` and validates `owner` relationship via `_get_user_sailing_event_or_404`.
- **Websocket**: Broadcasts `EVENT_CREW_UPDATED` with the `se.id` (sailing event ID) upon successful commit.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Triggers `evaluate_roster` if a crew member is declined; triggers an email notification via `_notify`.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.markCrewResponse` (Web frontend).
