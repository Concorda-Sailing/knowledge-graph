---
node_id: concorda-web::src/components/dashboard/events-calendar.tsx::groupEventsByMonth
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 17106982fbec80ff0c06316e918388400ae0e1d63da0104c4d87c210a08aeb3d
status: llm_drafted
---

# groupEventsByMonth

## Purpose

The `groupEventsByMonth` helper organizes an array of `Event` objects into a dictionary keyed by a "YYYY-MM" string. It is used to drive the calendar view in the `EventsCalendar` component, ensuring events are bucketed by their occurrence in the organization's local timezone rather than the user's browser time.

## Invariants

- **Input is an array of `Event` objects and a `tz` string.** The `tz` must be a valid IANA timezone string.
- **Keys are formatted as `"YYYY-MM"`.** The month component is zero-padded (e.g., `"2026-05"`).
- **Events are sorted chronologically within each month.** The function uses `new Date(a.date).getTime()` to ensure the internal array order is deterministic.
- **Relies on `ymdInOrgTz` for bucketing.** The grouping logic is strictly dependent on the output of `ymdInOrgTz` to ensure the calendar grid aligns with the organization's temporal reality.

## Gotchas

- **Must use `ymdInOrgTz` for all date transformations.** Per commit `f444b4c`, failing to render backend datetimes in the organization's timezone (rather than the browser's local time) causes a mismatch between the event's perceived date and its position in the calendar grid.
- **Month indexing offset.** The function manually adds `1` to the month index (`ymd.month + 1`) to convert the 0-indexed JavaScript month to a 1-indexed human-readable string.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Drives the visual grouping and sorting of the `EventsCalendar` component.

## External consumers

None known.
