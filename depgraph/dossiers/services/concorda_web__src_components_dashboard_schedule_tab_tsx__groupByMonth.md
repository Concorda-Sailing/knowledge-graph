---
node_id: concorda-web::src/components/dashboard/schedule-tab.tsx::groupByMonth
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5e392bd4601f9ad71daa43c15ae020aa362f164fbbcdf05f2dfbe1edc7fddd4d
status: llm_drafted
---

# groupByMonth

## Purpose

The `groupByMonth` helper organizes a flat list of `ScheduleItem` objects into a `Map` keyed by a YYYY-MM string. It is used to drive the chronological rendering of the schedule tab, ensuring that items are grouped under a human-readable month label. Use this instead of manual grouping to ensure the `label` and `monthNum` are derived consistently from the organization's timezone.

## Invariants

- **Input must be a `ScheduleItem[]` and a valid `tz` string.**
- **Returns a `Map<string, { label: string; monthNum: number; items: ScheduleItem[] }>`**.
- **The Map key is a zero-padded string format** (`"YYYY-MM"`) used for stable sorting and lookups.
- **`label` is generated via `formatInOrgTz`** using the `{ month: "long" }` option to ensure the UI displays the full month name (e.g., "May") rather than just a number.

## Gotchas

- **Timezone dependency:** Per commit `f444b4c4`, this function relies on `ymdInOrgTz` and `formatInOrgTz`. If the `tz` passed is not the organization's timezone, the grouping keys and labels will drift from the actual event dates, potentially causing events to appear in the wrong month in the UI.
- **Empty/Invalid Dates:** If `ymdInOrgTz` returns a falsy value (e.g., for an invalid or missing date), the item is skipped via `if (!ymd) continue`. This prevents the function from throwing but may result in "missing" events in the UI if the date parsing fails.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Rebuilds the visual structure of the Schedule Tab.

## External consumers

None known.
