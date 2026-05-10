---
node_id: concorda-web::src/lib/api.ts::eventsApi.removeScheduleSeries
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c3a677f54423df83a998146b01ef3ebd3002b0c5c0f207b9bcad9a19ce2be6a7
status: current
---

# eventsApi.removeScheduleSeries

## Purpose

The `removeScheduleSeries` method handles the deletion of a recurring schedule series. It is used to remove an entire sequence of events from a user's schedule via a single `seriesUuid`. This is distinct from `removeScheduleEvent`, which targets a single specific instance.

## Invariants

- **HTTP Method is `DELETE`** — targets the specific series resource.
- **Endpoint path** follows the pattern `/api/events/my-schedule/series/${seriesUuid}`.
- **Returns a count-based object** — the response shape is `{ removed: number; crew_removed: number }`.
- **Requires authentication** — uses `fetchApiAuthenticated` to ensure the user has permission to modify their own schedule.

## Gotchas

- **Impacts both events and crew** — the return object tracks both the number of events removed and the number of crew members removed. This is critical for UI state updates that need to reflect both the schedule change and any associated crew changes.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to verify user identity and permissions.
- **Side effects**: Deleting a series will trigger updates in the `ScheduleTab` component (e.g., `schedule-tab.tsx:546`) to reflect the removal of the series and its constituent events.

## External consumers

None known.
