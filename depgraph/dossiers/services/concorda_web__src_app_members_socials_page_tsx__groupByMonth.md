---
node_id: concorda-web::src/app/members/socials/page.tsx::groupByMonth
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4fe00dbd0919865f61a9bdf012b6a386f0ad193896fbc7055d1b9615c0d30e53
status: current
---

# groupByMonth

## Purpose

Groups an array of `Event` objects into a `Map` keyed by a month-based string. This provides the structural foundation for the chronological calendar view in the Socials page, allowing events to be rendered under human-readable headers (e.g., "May 2026"). It relies on `formatDate` to generate the `monthKey` used for grouping.

## Invariants

- **Input must be an array of `Event` objects.**
- **`tz` (timezone) is required** to ensure the `monthKey` and `label` are calculated relative to the organization's timezone, not the user's browser.
- **Returns a `Map<string, { label: string; monthNum: number; events: Event[] }>`**.
- **The `monthKey` format is `YYYY-MM`** (e.g., `"2026-05"`), which ensures correct chronological sorting when iterating over the Map keys.
- **Events without a `date` property are skipped** during the grouping process.

## Gotchas

- **Timezone-dependent grouping:** Per commit `f444b4c`, all date processing must use the organization's timezone. If `tz` is not passed correctly or if `formatDate` uses the browser's local time, events near the start/end of a month may appear in the wrong group (e.g., an event occurring at 11 PM on the last day of the month in the org TZ might be grouped into the next month in the browser's local TZ).

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Drives the layout of the Socials calendar view.

## External consumers

None known.
