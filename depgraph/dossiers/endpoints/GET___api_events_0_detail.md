---
node_id: GET::/api/events/{0}/detail
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 94d516664832fa70778f933201cc640795cc2a8e685518f72bd17f7ea814a9df
status: current
---

# GET /api/events/{event_id}/detail

## Purpose

Provides the authoritative, scoped view of a single event's details for the UI. Unlike the general calendar feed, this endpoint implements strict authorization logic to ensure users can only see details for events they have a legitimate claim to (e.g., owner, bookmarker, registrant, or crew). It is the primary data source for the schedule detail page in the web app.

## Invariants

- **Method/Path**: `GET /api/events/{event_id}/detail`
- **Auth**: Requires a valid session via `require_auth`.
- **Authorization**: Returns `403` if the user lacks a valid claim (owner, bookmarker, registrant, crew, or boat-owner of assigned boat).
- **Error Handling**: Returns `404` if the `event_id` does not exist.
- **Return Shape**: Returns a dictionary representing the `ScheduleItem` for the specific event, scoped to the viewer.

## Gotchas

- **Authorization is stricter than the feed**: While the general "my-schedule" feed might show an event exists, this endpoint will return a `403` if the user's relationship to the event (e.g., as a crew member or boat owner) is not explicitly recognized by `_build_schedule_item_for_event`.
- **Role-based visibility**: Per commit `f88bd5a`, the `crew_boats` field is suppressed if the viewer is not in "crew mode," preventing accidental exposure of boat data to non-crew members.
- **Slug collision avoidance**: Per commit `4fd165d`, the API no longer uses slugs for personal events to avoid global `UNIQUE` constraint collisions in the database.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` dependency; access is gated by `_build_schedule_item_for_event`.
- **Side effects**: The data returned here populates the schedule detail page in `concorda-web`.

## External consumers

- `concorda-web` (via `eventsApi.getDetail`)
