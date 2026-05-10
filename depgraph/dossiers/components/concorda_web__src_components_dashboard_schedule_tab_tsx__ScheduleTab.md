---
node_id: concorda-web::src/components/dashboard/schedule-tab.tsx::ScheduleTab
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cc194387aecb39bf32f352218aeb1fa9ae7d9fece7cc7bde147e73d23ac1b7de
status: llm_drafted
---

# ScheduleTab

## Purpose

The `ScheduleTab` component renders the primary chronological view of upcoming races and events for an organization. It manages complex state for filtering (regions, weekdays, upcoming status), month-based navigation, and per-month collapse preferences. It is distinct from the general calendar view by providing a more granular, list-oriented interface with specialized controls for managing event visibility and user-specific display preferences.

## Invariants

- **Calendar anchoring is TZ-aware.** The `calendarMonth` must be seeded using `ymdInOrgTz` to ensure the view starts at the first of the organization's current month, not the browser's local month.
- **Filter state is ephemeral.** Filters like `filterRegions` and `filterWeekday` are held in local state and do not persist across sessions unless explicitly tied to a URL parameter or external store.
- **Month collapse state is a local override.** The `monthCollapseOverrides` map tracks which months are expanded/collapsed, allowing users to maintain a specific view without mutating global organization settings.

## Gotchas

- **Timezone drift in navigation.** Per commit `f444b4c`, all backend datetimes must be rendered in the organization's timezone. Using browser-local time for date arithmetic or display is a regression; always use `ymdInOrgTz` when calculating the start of a month.
- **Peer crew visibility.** Per commit `6eace6a`, the component must ensure that peer crew status is hidden from non-owner viewers to maintain privacy.
- **Empty state button duplication.** Per commit `b7067b5`, the "Add Sail" button logic was refined to prevent duplicate triggers when the empty state is active, as the top-level button already covers this action.

## Cross-cutting concerns

- **Auth**: Uses `useAuth` to determine user identity, which impacts visibility of certain crew/event details (see `6eace6a`).
- **Side effects**: Updates the `event` search parameter in the URL via `router.replace` when a specific event is selected, affecting the global routing state.

## External consumers

None known.

## Open questions

- The `monthCollapseOverrides` currently uses a local `Map` state; it is unclear if this should eventually be persisted to a backend preference service to allow the user's view preference to persist across sessions.
