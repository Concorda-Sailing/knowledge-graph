---
node_id: concorda-web::src/lib/api.ts::eventsApi.addEvents
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 233bfe0d1cd80e9f78bf946d4310e89788d92ce9551a36d9fede56ffef9d5234
status: current
---

# eventsApi.addEvents

## Purpose

Adds a batch of existing event IDs to the current user's personal schedule. This is distinct from `addEvents` in `seriesApi`, which creates entirely new event instances; `addEvents` simply links existing events to the user's timeline. Use this when a user wants to "follow" or "track" a specific regatta or event series.

## Invariants

- **Method is `POST`** to `/api/events/my-schedule/add-events`.
- **Payload requires `event_ids`** as an array of strings.
- **Returns an object** containing the count of successfully added events: `{ added: number }`.
- **Requires authentication** via `fetchApiAuthenticated`.

## Gotchas

- **Dependency on `boat_uuid`**: Per commit `f876f14`, ensure that if this is used in a flow involving crew requests, the `boat_uuid` is passed through correctly to avoid schema mismatches in the backend.
- **Coupling to `my-schedule`**: Unlike the general `eventsApi` methods that target specific `eventId`s, this endpoint is scoped to the user's personal schedule.

## Cross-cutting concerns

- **Auth**: Uses `fetchApi-authenticated` to ensure the user is logged in and has permission to modify their own schedule.
- **Side effects**: Successfully adding events will update the user's personal schedule view and may trigger updates to the "my-schedule" dashboard components.

## External consumers

None known.
