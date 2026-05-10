---
node_id: concorda-web::src/app/members/admin/analytics/page.tsx::AnalyticsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 49733e0785c31865b798fb97da630c3e0937f588093fff30a5b260ab2752c759
status: current
---

# AnalyticsPage

## Purpose

The high-level entry point for the administrative analytics dashboard. It wraps the `AnalyticsContent` component in a `PermissionGate` to ensure only users with the `admin.users.view` permission can access usage statistics, active user counts, and endpoint performance data.

## Invariants

- **Permission Guard**: Access is strictly gated by `PermissionGate` with the `admin.users.view` permission.
- **Timezone-Aware Range Calculation**: The `presetRange` function must use the organization's timezone (via `ymdInOrgTz`) rather than the user's local browser time to ensure the "Today" or "This Month" boundaries align with the backend data.
- **Date Arithmetic**: Date offsets (e.g., `dayBack`) are calculated using `Date.UTC` to prevent local timezone shifts from causing off-by-one errors in the ISO strings sent to the API.

## Gotchas

- **Timezone Drift**: Per commit `f444b4c`, all backend datetime rendering and range calculations must be explicitly tied to the organization's timezone. Failing to do so results in the dashboard showing the wrong "current" window for users in different timezones.
- **ISO String Construction**: The `toIsoDate` helper manually constructs strings (e.g., `y-m-d`). If the month or day is not zero-padded, the resulting string will fail to match the expected ISO format for the API.

## Cross-cutting concerns

- **Auth**: Requires `admin.users.view` permission via `PermissionGate`.
- **Side effects**: Displays high-level usage stats (EndpointStat, ActiveUser, DailyActivity, OnlineUser) which are used by admins to monitor system health and user engagement.

## External consumers

None known.
