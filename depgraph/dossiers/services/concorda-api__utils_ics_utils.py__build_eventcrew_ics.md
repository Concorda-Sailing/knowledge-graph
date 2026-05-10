---
node_id: concorda-api::utils/ics_utils.py::build_eventcrew_ics
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ceeeb30a19d99d8d25a0512769ced8fa30b10c4912f3f43dfed2aaa05fa441ab
status: llm_drafted
---

# build_eventcrew_ics

## Purpose

Generates a single-event RFC 5545 compliant `.ics` string for an `EventCrew` row. It wraps the event data into a full calendar object (including `VEVENT` and `VCALENDAR` headers) to support both `REQUEST` and `CANCEL` methods. Use this when a user needs to sync a specific crew commitment or registration to their personal calendar.

## Invariants

- **Input is `CrewIcsContext`** — requires `method`, `tz_id`, and the event data via `_vevent`.
- **Output is a single-event calendar** — returns a string with `BEGIN:VCALENDAR` and `END:VCALENDAR` delimiters.
- **All-day events use `VALUE=DATE`** — if `dock_time` is `None`, the function uses `DTSTART;VALUE=DATE` and `DTEND;VALUE=DATE` to ensure the event is treated as a full-day event in the target calendar.
- **`DTEND` is exclusive for all-day events** — per RFC 5545, the `end_date` is incremented by one day to ensure the event covers the intended date range.

## Gotchas

- **Timezone-aware rendering** — per commit `6c314f5`, this must render in the organization's timezone (`tz_id`) rather than UTC to prevent shifts in the user's calendar.
- **`DTEND` calculation for timed events** — if `arrival_time` is missing, the function falls back to `dock_time + estimated_duration`. If `estimated_duration` is also missing, it defaults to `DEFAULT_TIMED_DURATION`.
- **UID preservation** — the `uid` is provided by the caller (not generated here) to ensure that `CANCEL` methods correctly target the existing event rather than creating a duplicate or a new entry.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: None known.

## External consumers

None known.
