---
node_id: concorda-web::src/lib/api.ts::eventsApi.addSeries
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 25ebd356510c2cee954cfcaa4aedbc777753520cc2fdb7e440d077f7e831e9b1
status: current
---

# eventsApi.addSeries

## Purpose

The `addSeries` method handles the creation of a recurring event series (regattas) within a user's schedule. It allows a user to batch-create or link multiple sailing events under a single series umbrella, optionally specifying a boat, departure/dock times, or a crew pool. Use this when a user is transitioning from a single event to a multi-race commitment.

## Invariants

- **Method is POST** to `/api/events/my-schedule/add-series`.
- **Requires `series_uuid`** as a string.
- **`dock_time` and `departure_time`** must be in `"HH:MM"` 24h format.
- **`estimated_duration`** is a decimal string (e.g., `"2.5"`).
- **Returns a structured object** containing `{ added: number; sailing_events_created: number; total_races: number }`.
- **Uses `fetchApiAuthenticated`** to ensure the user's session is valid and the request is authorized.

## Gotchas

- **`boat_uuid` is optional for "as crew" flows.** If `boat_uuid` is omitted, the system treats the entry as a bookmark/participation record without a formal boat setup.
- **`requestToCrew` dependency:** Per commit `f876f14`, ensure that if a user is requesting to join a crew, the `boat_uuid` is passed through the request body to avoid malformed payloads.
- **Type-safety for `estimated_duration`:** The API expects a string representation of a decimal (e.g., `"2.5"`) rather than a raw number, to ensure consistent parsing of duration.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to verify user identity and permissions.
- **Side effects**: Triggers updates to the "accepting-crew" status and the "schedule card" view (per commit `2d6b8a7`).

## External consumers

None known.
