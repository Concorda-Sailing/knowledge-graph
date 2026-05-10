---
node_id: concorda-web::src/components/admin/response-time-drilldown.tsx::formatBucketTick
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bbee7d4cbf70602608e40b7fcdf41d4969ac72d442e3ad687058d5542e72a85e
status: llm_drafted
---

# formatBucketTick

## Purpose

Calculates the visual label for time-series chart ticks based on the temporal density of the view. It selects a format that balances readability with the available horizontal space, switching from a time-only format to a date-inclusive format as the time window expands. This ensures the chart axis remains legible regardless of whether the user is looking at a 1-hour window or a multi-day window.

## Invariants

- **Input `iso` is a UTC string.** The function assumes the input is a valid ISO timestamp.
- **Output is a display string.** The result is intended for a chart axis and is not a Date object.
- **Format scales with `hours`.** If `hours <= 24`, it returns only time (`hour` and `minute`). If `hours > 24`, it prepends the `month` and `day` to the time.
- **Uses `formatInOrgTz` for localization.** All time rendering must be passed through the organization's timezone helper to ensure consistency with the rest of the admin dashboard.

## Gotchas

- **Backend datetime normalization.** Per commit `f444b4c`, the system must ensure backend datetimes are rendered in the organization's timezone rather than the browser's local time. While this function handles the formatting, the underlying `iso` string must be correctly treated as UTC to avoid offset errors.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
