---
node_id: concorda-web::src/app/members/regattas/page.tsx::formatDate
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2bdb6b16f39b21f8428b296a83af656eab5b21fe46a1464b35a963c3f5461e02
status: llm_drafted
---

# formatDate

## Purpose

A local helper function that transforms a UTC ISO date string into a structured object containing localized display components (day, day of week, month, and year). It is used primarily by `groupByMonth` to create the grouping keys and labels for the regatta schedule view. It acts as a bridge between the raw string and the UI-ready components like `ymdInOrgTz` and `formatInOrgTz`.

## Invariants

- **Input is a UTC ISO string** (`dateStr`) and a timezone string (`tz`).
- **Returns a structured object** containing `day`, `dayOfWeek`, `month`, `monthNum`, `year`, and `monthKey`.
- **`monthKey` follows the format `YYYY-MM`** (e.g., `"2026-05"`) to ensure stable Map keys during grouping.
- **Fallback state:** If `ymdInOrgTz` returns a falsy value, the function returns an object with zeroed/empty values (`day: 0`, `month: ""`, etc.) rather than throwing, to prevent breaking the `groupByMonth` loop.

## Gotchas

- **Must use organization timezone, not browser local.** Per commit `f444b4c`, this function is critical for ensuring all backend datetimes are rendered in the org's specific timezone. If a developer uses a standard `new Date().toLocale...` approach instead of this helper, the regatta schedule will display the wrong dates for users in different timezones.
- **`monthKey` padding is mandatory.** The `monthKey` relies on `String(ymd.month + 1).padStart(2, "0")` to ensure that months like January are represented as `"01"` rather than `"1"`. This is required for the `Map` in `groupByMonth` to sort and group correctly.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Drives the grouping logic for the regatta schedule calendar/list view.

## External consumers

None known.
