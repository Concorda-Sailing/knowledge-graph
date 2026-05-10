---
node_id: concorda-web::src/app/members/socials/page.tsx::SocialsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 95cf987a4e15f33ce7a7e2f3db0d47430b1bdfae21b560da214306929bedfcd5
status: llm_drafted
---

# SocialsPage

## Purpose

The primary view for members to interact with social events and personal schedules. It aggregates data from `socialsApi.list()` and `eventsApi.mySchedule()` to present a unified view of upcoming social engagements and personal race calendars. It provides filtering by region, day-type (weekday/weekend), and search capabilities to manage high-density event lists.

## Invariants

- **Calendar anchoring is organization-centric.** The `calendarMonth` state must be anchored to the first of the current month in the organization's timezone via `ymdInOrgTz`, not the user's local browser time.
- **Data fetching is dual-source.** It concurrently fetches social events and the user's specific schedule to allow for the `scheduleBySource` lookup mapping.
- **Filtering is additive.** The `hasActiveFilters` flag is a boolean OR of the search string, `hidePast` toggle, region set size, and weekday/weekend toggles.
- **Sorting is chronological.** The `sorted` memoized array always orders events by their date timestamp in ascending order.

## Gotchas

- **Timezone-driven calendar drift.** Per commit `f444b4c`, the calendar must anchor at the first of the *org-TZ* current month. If the `ymdInOrgTz` helper or the `timezone` constant is missing, the calendar view will display the wrong month for users in different timezones, breaking the visual alignment of the month grid.
- **Silent failure on schedule fetch.** The `load` function catches errors on `eventsApi.mySchedule()` and returns an empty array `[]` rather than throwing. This prevents the entire page from crashing if the user has no schedule, but it means a failed API call results in a silent empty state rather than an error UI.

## Cross-cutting concerns

- **Auth**: Relies on `eventsApi.mySchedule()` which requires a valid authenticated session (bearer token).
- **Side effects**: Rebuilds the view when `events` or `schedule` state changes; affects the visibility of the "Socials" dashboard view.

## External consumers

None known.
