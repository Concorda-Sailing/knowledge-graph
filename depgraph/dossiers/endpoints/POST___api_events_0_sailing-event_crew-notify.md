---
node_id: POST::/api/events/{0}/sailing-event/crew-notify
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7a6712a3d3ab2c7d95e96068bfba35460a1bb800701c38bc0b27854a30dd5001
status: llm_drafted
---

# POST /api/events/{event_id}/sailing-event/crew-notify

## Purpose

Triggers the notification flow for all crew members assigned to a specific sailing event. It transitions crew members from the 'pool' status to 'invited' and executes the necessary notification logic via `services.crew_roster.notify_crew`. Use this endpoint when an owner wants to formally move the roster from a pending state to an active, notified state.

## Invariants

- **Requires `owner` relation** — The `_get_user_sailing_event_or_404` check ensures only the event owner can trigger this notification.
- **Returns a list of `EventCrewRead` objects** — The response body contains the updated state of the crew members who were just notified.
- **Triggers a broadcast** — Emits `EVENT_CREW_UPDATED` via `broadcast_event` upon successful commit.
- **Atomic DB commit** — The function performs a `db.commit()` after the service call to ensure the status transition and notifications are treated as a single unit of work.

## Gotchas

- **Status transition dependency** — This endpoint is the primary driver for moving users out of the "pool" state. If the logic in `services.crew_roster.notify_crew` is altered, the transition from `pool` to `invited` may fail or behave unexpectedly.
- **Ownership requirement** — Unlike some other event endpoints, this strictly requires the `relation="owner"` check; attempting to call this as a co-owner or viewer will result in a 404 or 403 via `_get_user_sailing_event_or_404`.

## Cross-cutting concerns

- **Auth**: Requires authenticated user with `owner` relation to the event.
- **Websocket**: Emits `EVENT_CREW_UPDATED` for the specific `event_id`.
- **Side effects**: Triggers updates to the crew roster visibility and potentially updates the "crew count" or status indicators in the UI.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.notifyCrew`
