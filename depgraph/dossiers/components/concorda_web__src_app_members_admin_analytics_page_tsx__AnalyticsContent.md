---
node_id: concorda-web::src/app/members/admin/analytics/page.tsx::AnalyticsContent
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b942403070027277eb0a4be18d2dd1711d0e4e592725aaa3b1ca31d3cbf1ed9f
status: current
---

# AnalyticsContent

## Purpose

The `AnalyticsContent` component renders the administrative dashboard for site usage statistics. It manages the state for date range selection (via `PRESETS`) and orchestrates concurrent API calls to fetch summary data, endpoint statistics, active user counts, and real-time online user status. It is the primary view for administrators to monitor system load and user engagement.

## Invariants

- **Date range synchronization**: The `start` and `end` states are driven by the `presetRange` helper, which must receive the organization's `timezone` to ensure the date boundaries align with the backend's UTC-based storage.
- **Concurrent fetching**: The component uses `Promise.all` to fetch five distinct metrics (`summary`, `topEndpoints`, `activeUsers`, `dailyActivity`, and `onlineNow`) to minimize loading-state duration.
- **Loading state fallback**: If `loading` is true and no `summary` has been successfully fetched, the component renders a skeleton UI to prevent layout shift.

## Gotchas

- **Timezone-aware boundaries**: Per commit `f444b4c`, all date ranges passed to `analyticsApi` must be calculated using the organization's timezone via `presetRange(key, timezone)` rather than the browser's local time to prevent off-by-one-day errors in the rendered data.
- **Empty catch block**: The `load` function contains an empty `catch` block (lines 111-112). If any of the five concurrent API calls fail, the component will remain in a loading state or fail to update the UI without explicit error feedback.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges (implied by the `members/admin` path).
- **Side effects**: Updates the visibility of the "Site usage and activity" dashboard.

## External consumers

None known.
