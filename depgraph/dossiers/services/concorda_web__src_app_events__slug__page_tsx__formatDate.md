---
node_id: concorda-web::src/app/events/[slug]/page.tsx::formatDate
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e0ff07bbe48cb34872fa460d25b39ade58d35f711a78f112fe895bc2cb106492
status: llm_drafted
---

# formatDate

## Purpose

A local helper for formatting event timestamps into human-readable strings. It wraps `formatInOrgTz` to ensure that date and time strings are rendered using the organization's specific timezone rather than the user's local browser time. Use `formatDate` for full date strings (weekday, year, month, day) and `formatTime` for time-only strings (hour, minute).

## Invariants

- **Input is a UTC ISO string.** The `dateStr` must be a valid ISO timestamp to be processed correctly by the underlying `formatInOrgTz`.
- **Output is a localized string.** The return value is a display-ready string (e.g., "Monday, January 1, 2024") and is not intended for further date manipulation.
- **Requires `tz` parameter.** The `tz` argument must be the organization's timezone string (e.g., `America/New_York`) to ensure consistency across the event page.

## Gotchas

- **Avoid browser-local time.** Per commit `f444b4c`, all backend datetimes must be rendered in the organization's timezone. Using native `Date` methods or failing to pass the `tz` through `formatInOrgTz` will result in the UI showing the wrong date/time for users in different timezones.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
