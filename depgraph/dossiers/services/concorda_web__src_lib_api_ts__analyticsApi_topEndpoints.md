---
node_id: concorda-web::src/lib/api.ts::analyticsApi.topEndpoints
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 52c43a774e89887ee76818c95ed7f3ac486cdd5d8d7e568dec5dff6053b8b7af
status: current
---

# analyticsApi.topEndpoints

## Purpose

Provides access to high-level analytical data regarding system usage and user activity. This object contains methods for fetching aggregated statistics (summaries, top endpoints, and daily activity) and real-time user presence. It is distinct from the `mediaApi` or `eventsApi` by focusing on system-wide telemetry rather than specific entity manipulation.

## Invariants

- **Requires authentication** — All methods utilize `fetchApiAuthenticated` and require a valid session.
- **Time-range dependent** — `summary`, `topEndpoints`, `activeUsers`, and `dailyActivity` all require `start` and `end` ISO strings as arguments to define the window of analysis.
- **Return types are strictly typed** — Methods return specific arrays (e.g., `EndpointStat[]`, `ActiveUser[]`, `DailyActivity[]`) to ensure the admin UI can render statistical charts correctly.
- **`onlineNow` is parameterless** — Unlike the other methods, it does not accept a time range and returns the current real-time state.

## Gotchas

- **Admin-only visibility** — While the API is authenticated, the data returned (especially `activeUsers` and `topEndpoints`) is intended for the admin dashboard.
- **Time-range precision** — Because `start` and `end` are passed as template literals in the query string, ensure the date format is a valid ISO string to avoid API rejection.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Data from these endpoints is consumed by the `AnalyticsContent` component in the admin dashboard (`src/app/members/admin/analytics/page.tsx`).

## External consumers

None known.
