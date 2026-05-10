---
node_id: concorda-web::src/app/members/admin/files/page.tsx::formatDate
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: eb5ffe976f589922b2e13f6af54ad4a69d2d90a60987d0ab4bb615cfe46969ed
status: current
---

# formatDate

## Purpose

A local helper function used to format ISO date strings into a human-readable format localized to the organization's timezone. It wraps `formatInOrgTz` with a specific preset of `{month: "short", day: "numeric", year: "numeric"}`. Use this instead of raw date formatting to ensure the Admin Files page displays consistent, non-browser-local time-of-upload/modification data.

## Invariants

- **Input is a UTC ISO string.** The function expects a valid date string to pass to the underlying formatter.
- **Output is a localized string.** It returns a string like "Jan 1, 2025" rather than a Date object.
- **Uses the organization's timezone.** It explicitly passes the `tz` argument to `formatInOrgTz` to avoid the viewer's local time drift.

## Gotchas

- **Must use `formatInOrgTz` via this helper.** Per commit `f444b4c`, all backend datetimes must be rendered in the organization's timezone. Using a standard `toLocaleDateString()` or a different formatting utility will violate the requirement to never render browser-local time for admin assets.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Affects the visual representation of file upload/modification timestamps in the `AdminFilesPage` table.

## External consumers

None known.
