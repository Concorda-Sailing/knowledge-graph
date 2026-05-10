---
node_id: concorda-web::src/app/members/admin/events/import/page.tsx::formatFriendly
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7126a739df991a251b55c51d9e5d0783eff3a0825e8708e2328b2f9d6b69031e
status: current
---

# formatFriendly

## Purpose

Converts a UTC ISO date string into a human-readable, localized string using the organization's specific timezone. It is used within the event import UI to provide a "friendly" preview of the date being processed. This is distinct from the global `formatInOrgTz` helper because it is a localized, single-use display function specific to the import page's preview logic.

## Invariants

- **Input is a string.** Accepts a `dateStr` (expected to be ISO 8601) and a `tz` string.
- **Fallback behavior.** If the input is empty, returns `""`. If the input is an invalid date string that cannot be parsed, it returns the original `dateStr` rather than an error or empty string.
- **Output format.** Returns a string containing the weekday, month, day, year, and 2-digit minutes (e.g., "Wed, May 8, 2026, 10:30 AM").
- **Timezone-aware.** Uses `Intl.DateTimeFormat` via `toLocaleDateString` to ensure the display matches the provided `tz` rather than the user's local browser time.

## Gotchas

- **Avoid browser-local drift.** Per commit `f444b4c`, this function must always receive the organization's timezone as the `tz` argument to prevent the UI from showing the viewer's local time instead of the event's actual time.
- **Parsing fragility.** Because it uses `new Date(dateStr)`, it relies on the input being a valid ISO string. If the input is a malformed string that `new Date()` can technically parse but is logically incorrect, the output will reflect that incorrectness.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Used for previewing data during the spreadsheet multi-import process.

## External consumers

None known.
