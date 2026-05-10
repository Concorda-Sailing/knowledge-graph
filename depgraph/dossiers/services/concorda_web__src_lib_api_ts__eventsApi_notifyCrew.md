---
node_id: concorda-web::src/lib/api.ts::eventsApi.notifyCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 07f50a7804e522a8f5e5d4088ed971efffe14e448d191bcc34c9cb8f94b32d5c
status: current
---

# eventsApi.notifyCrew

## Purpose

Triggers a notification to the current crew members for a specific event. This is a POST request used to broadcast status updates or alerts to the established crew pool. Use this when the UI needs to signal that a change in event state or a specific requirement has occurred that requires the crew's attention.

## Invariants

- **Method is POST** — Unlike the sibling `getEventCrew` (GET) or `setCrewPool` (PUT), this is a terminal action that triggers a side-effect notification.
- **Requires `eventId`** — The endpoint is scoped strictly to the event hierarchy: `/api/events/${eventId}/sailing-event/crew-notify`.
- **Returns `EventCrewMember[]`** — The response provides the list of members who were notified, allowing the UI to confirm the broadcast was successful.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to execute.

## Gotchas

- **Dependency on `boat_uuid`** — Per commit `f876f14`, the related `requestToCrew` logic requires `boat_uuid` to be passed through correctly; ensure that any logic leading up to a crew notification (like a request) has correctly handled the boat context to avoid broken flows.
- **Status vs. Count** — Per commit `b4d60c6`, there is a distinction between "accepted invites" and "live slot counts." Ensure that notifying the crew is not being used as a proxy for state-checking that should be handled by the server-side count.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Triggers notifications that may affect the visibility of status badges on the `EventCrewCard` component.

## External consumers

- `EventCrewCard` (via `event-crew-card.tsx:101`)
