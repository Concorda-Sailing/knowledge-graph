---
node_id: concorda-web::src/components/dashboard/events-calendar.tsx::EventsCalendar
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2211d9893fbce5a69cfd8df12b2809591391960b6c26faba402352c281a2d9a3
status: llm_drafted
---

# EventsCalendar

## Purpose

The `EventsCalendar` component provides a visual grid representation of events, allowing users to toggle between a calendar view and a list view. It is responsible for grouping and displaying events based on the organization's specific timezone rather than the user's local browser time. Use this component when a dashboard view requires a temporal overview of events that must align with the organization's local calendar logic.

## Invariants

- **Timezone-driven bucketing** — Events are grouped into cells using `ymdInOrgTz` to ensure the visual date matches the organization's local day.
- **`calendarMonth` state** — The view is anchored to a specific month/year, calculated using the organization's timezone to prevent the calendar from shifting based on the viewer's location.
- **Input is an array of `Event` objects** — These must include `date` and optionally `end_date` strings.
- **`getMonthLabel` uses UTC** — The month label is rendered using a UTC anchor to ensure the string representation matches the `YYYY-MM` key exactly.

## Gotchas

- **Timezone mismatch risk** — Per commit `f444b4c`, all backend datetimes must be rendered in the organization's timezone. If you use standard `Date` methods or `toLocaleString()` without passing the organization's timezone via `ymdInOrgTz`, the calendar cells will display the wrong dates for users in different timezones.
- **`ymdKey` calculation** — The component uses a numeric integer `(year * 10000 + month * 100 + day)` for cell identity. This is a critical internal mechanism for filtering events into the correct grid cells.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Rebuilds the visual state of the dashboard when `region` or `onRegionChange` is triggered.

## External consumers

None known.
