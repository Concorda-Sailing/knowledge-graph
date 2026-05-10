---
node_id: concorda-web::src/app/members/admin/analytics/page.tsx::presetRange
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7d7125df27d16577e3127ee96450e7e4e301eb9367aabdf24db8cff63d60b572
status: llm_drafted
---

# presetRange

## Purpose

Calculates date boundaries for analytics queries based on a specific organization's timezone. It maps high-level presets (like "7d" or "lastMonth") to specific ISO-formatted date strings to ensure the backend receives a time window that matches the organization's local day, rather than the viewer's browser time.

## Invariants

- **Input `tz` is mandatory.** The function requires a valid timezone string to calculate the current "today" via `ymdInOrgTz`.
- **Returns ISO-8601 strings.** The `start` and `end` properties are always formatted as `YYYY-MM-DD` strings via `toIsoDate`.
- **Uses UTC for arithmetic.** Date subtraction (e.g., `dayBack`) is performed using `Date.UTC` to prevent day-stepping errors caused by local browser offsets.
- **`today` is derived from the organization.** The calculation of "today" must use the organization's timezone to ensure consistency between different admins viewing the same dashboard.

## Gotchas

- **Must not use browser-local time.** Per commit `f444b4c`, all date-related logic must be anchored to the organization's timezone. An admin in a different timezone (e.g., PT) viewing an ET organization's analytics must see the same date range as an ET-based admin.
- **`ymdInOrgTz` failure mode.** If `ymdInOrgTz` returns null (due to an invalid or missing timezone), the function returns `{ start: "", end: "" }`. Callers must handle these empty strings to avoid sending malformed requests to the `analyticsApi`.

## Cross-cutting concerns

- **Auth**: Relies on `PermissionGate` (in the parent component) to ensure only authorized admins access the resulting analytics data.
- **Side effects**: The output of this function directly drives the `start` and `end` parameters for all `analyticsApi` calls (e.g., `summary`, `topEndpoints`, `activeUsers`).

## External consumers

None known.
