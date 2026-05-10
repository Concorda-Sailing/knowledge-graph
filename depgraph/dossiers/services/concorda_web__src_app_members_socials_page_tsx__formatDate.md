---
node_id: concorda-web::src/app/members/socials/page.tsx::formatDate
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bad227fcaf6c49459691f576b221d98421e02e085ff160d850c51d38c997de1b
status: current
---

# formatDate

## Purpose

The `formatDate` function is a specialized utility for decomposing a UTC ISO string into a structured object of localized date and time components. It is used to drive the grouping logic in the Socials calendar view. Unlike the general `formatInOrgTz` helper, this function returns a specific object shape (including `monthKey` and `dayOfWeek`) required for the `groupByMonth` function to bucket events correctly by month and year.

## Invariants

- **Input is a UTC ISO string** and a timezone string (`tz`).
- **Returns a structured object** containing `day`, `dayOfWeek`, `month`, `monthNum`, `year`, `time`, and `monthKey`.
- **`monthKey` format is strictly `YYYY-MM`** (e.g., `"2026-05"`) to ensure stable grouping in the `Map` used by `groupByMonth`.
- **Fallback behavior:** If `ymdInOrgTz` returns a falsy value, the function returns an object with zeroed/empty values (`day: 0`, `month: ""`, etc.) rather than throwing, to prevent breaking the `groupByMonth` loop.

## Gotchas

- **Strict reliance on `ymdInOrgTz` and `formatInOrgTz`**: Per commit `f444b4c`, all backend datetimes must be rendered in the organization's timezone rather than the browser's local time to ensure consistency across different users. If you modify this to use standard `Intl` methods without passing the `tz` through the specialized helpers, you will break the calendar's temporal accuracy.
- **`monthKey` padding**: The `monthKey` uses `String(ymd.month + 1).padStart(2, "0")`. If the logic for generating this key is changed (e.g., removing the padding), the `groupByMonth` function will fail to group events correctly, as the keys in the `Map` will no longer match.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Directly affects the grouping and rendering of the Socials calendar view.

## External consumers

None known.
