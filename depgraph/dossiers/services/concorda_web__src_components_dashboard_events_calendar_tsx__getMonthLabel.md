---
node_id: concorda-web::src/components/dashboard/events-calendar.tsx::getMonthLabel
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5f59e64bd85ae86db212dd5efba4422774b5d590508177ec59fd582b08e51078
status: current
---

# getMonthLabel

## Purpose

Converts a `"YYYY-MM"` string key into a human-readable month and year label (e.g., "January 2024"). It is a pure formatting helper used to label the grouping headers in the `EventsCalendar`. It is distinct from `ymdInOrgTz` because it does not perform timezone conversion; instead, it treats the input as a UTC anchor to ensure the rendered text matches the digits in the `monthKey` exactly.

## Invariants

- **Input format is strictly `"YYYY-MM"`**. The function expects a string that can be split into two parts.
- **Uses UTC for the anchor.** The `utcAnchor` is constructed using `Date.UTC` to prevent local timezone offsets from shifting the month or year during the `Intl.DateTimeFormat` execution.
- **Returns a localized string.** The output is a string formatted via `en-US` locale with `month: "long"` and `year: "numeric"`.

## Gotchas

- **Avoid local timezone drift.** Per commit `f444b4c`, the calendar must render labels based on the UTC representation of the key to ensure the UI matches the data. If this function were to use a local date constructor without the UTC anchor, the month label could shift (e.g., a December key appearing as November in certain timezones).

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Used by `EventsCalendar` to render the grouping headers for the event list/grid.

## External consumers

None known.
