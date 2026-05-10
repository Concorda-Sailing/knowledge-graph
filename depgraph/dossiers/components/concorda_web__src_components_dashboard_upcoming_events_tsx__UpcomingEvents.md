---
node_id: concorda-web::src/components/dashboard/upcoming-events.tsx::UpcomingEvents
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2eb3897023ae9f276e73484d630e31fecd670e0af2684144a2ff9a6ad3756e36
status: current
---

# UpcomingEvents

## Purpose

Displays a list of upcoming events and the user's current registrations. It provides a high-level overview of the schedule, grouped by month, and allows users to filter the view by geographic region. Use this component when a user needs to see what is coming up in their specific area without navigating to the full calendar.

## Invariants

- **Fetches two distinct data streams**: `eventsApi.upcoming` for the event list and `profileApi.getEventRegistrations` for the user's personal status.
- **Filters registrations locally**: Uses `isFuture(parseISO(r.event_date))` to ensure only upcoming registrations are shown, preventing past events from cluttering the dashboard.
- **Region state is persistent**: The `region` state is synchronized with `localStorage` via the `REGION_STORAGE_KEY` ("events_region_filter").
- **Month grouping is timezone-aware**: Uses `ymdInOrgTz` and `formatInOrgTz` to ensure the month labels and groupings match the organization's local time, not the user's browser time.

## Gotchas

- **Timezone rendering requirement**: Per commit `f444b4c`, all backend datetimes must be rendered using the organization's timezone via `ymdInOrgTz` and `formatInOrgTz`. Failing to do so will cause the month grouping to drift or display incorrect labels for users in different timezones.
- **Initialization race condition**: The component uses an `initialized` state to prevent the `useEffect` from firing before the `localStorage` value for `region` is loaded.

## Cross-cutting concerns

- **Auth**: Implicitly depends on `profileApi.getEventRegistrations` being called by an authenticated user.
- **Side effects**: Updates the user's view of the dashboard; changes to the `region` filter affect the list of events displayed.

## External consumers

None known.
