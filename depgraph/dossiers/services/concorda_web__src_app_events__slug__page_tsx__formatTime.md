---
node_id: concorda-web::src/app/events/[slug]/page.tsx::formatTime
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4b3315dbe9c6a1d7783fa5873501fd50aaa3964899f35248dc4df35d4b9f141e
status: current
---

# formatTime

## Purpose

A specialized time-formatting helper that converts a UTC ISO string into a localized time string (hour and minute). It is a sibling to `formatDate` and is used specifically when the date is already implied by context (e.g., in a list of event-specific times) to avoid redundant date rendering. It wraps `formatInOrgTz` to ensure the time is rendered in the organization's timezone rather than the user's local browser time.

## Invariants

- **Input is a UTC ISO string.** It expects a valid datetime string to parse.
- **Output is a display string.** It returns a string containing the hour and 2-digit minutes (e.g., "10:30 AM").
- **Uses `formatInOrgTz`.** It relies on the organization's timezone via the `tz` argument to maintain consistency across the event page.

## Gotchas

- **Must use organization timezone.** Per commit `f444b4c`, all backend datetimes must be rendered in the org TZ to prevent the UI from showing the wrong time to users in different locations. Never allow the browser's local time to dictate the output.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: None.

## External consumers

None known.
