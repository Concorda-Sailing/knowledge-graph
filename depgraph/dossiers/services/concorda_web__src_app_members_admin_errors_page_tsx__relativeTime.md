---
node_id: concorda-web::src/app/members/admin/errors/page.tsx::relativeTime
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 858c4f9f10459957d4bf667f0190bbc0449caccea97c8af582a0672d546d0bca
status: llm_drafted
---

# relativeTime

## Purpose

A local utility function that converts an ISO timestamp into a human-readable relative time string (e.g., "5m ago", "2h ago"). It is used exclusively within the `ErrorLogPage` to provide temporal context for captured exceptions and rate-limit events. This is a lightweight, client-side-only formatter and should not be used for complex date manipulation or timezone-aware rendering.

## Invariants

- **Input is an ISO string.** The function expects a valid UTC ISO string to calculate the delta from `Date.now()`.
- **Output is a string.** Returns a string containing the duration and the suffix "ago".
- **Uses `Date.now()` for delta calculation.** The relative time is calculated based on the exact moment the function is executed on the client.

## Gotchas

- **Does not account for clock skew.** Because it uses `Date.now()` on the client, if the user's system clock is significantly behind the server's time, the function may return negative values or unexpected results (though the current implementation does not explicitly guard against negative `ms`).
- **Loss of precision.** The function rounds to the nearest whole unit (seconds, minutes, hours, days) and does not provide sub-second or sub-minute precision.

## Cross-cutting concerns

- **Auth**: Requires `admin.audit.view` permission via the `SettingsPage` wrapper to ensure the error logs are only visible to authorized admins.
- **Audit**: Displays data fetched from `adminErrorLogApi.list`, which tracks 5xx exceptions and 429 rate-limit events.
- **Side effects**: The `ErrorLogPage` uses this to render the timestamp for error rows; changes to the rounding logic will change the visual density of the error log list.

## External consumers

None known.
