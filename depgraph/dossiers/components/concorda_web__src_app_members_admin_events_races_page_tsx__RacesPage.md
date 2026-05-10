---
node_id: concorda-web::src/app/members/admin/events/races/page.tsx::RacesPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0f2f9715a3b11e1cbbb4ff109ec616e6da1d9420dc5d5b52d6c7ffbd93460fb5
status: llm_drafted
---

# RacesPage

## Purpose

The administrative dashboard view for managing regattas (races). It provides a high-level overview of all races, allowing admins to filter by year, month, course type, or qualifier, and sort by various attributes. It serves as the primary entry point for navigating to specific race management or deletion flows.

## Invariants

- **Data Source**: Fetches all race data via `regattaApi.list()`.
- **State Management**: Uses `RegattaDetail[]` to drive the UI; any change to the `regattaApi` response shape will break the `monthTabs` and `years` memoized calculations.
- **Filtering Logic**: The `activeFilter` (month/year) is strictly tied to the `selectedYear`. If the `activeFilter` year does not match the `selectedYear`, the filter is automatically cleared.
- **Sorting**: Default sort order is `date` in `desc` direction.
- **Deletion**: `handleDelete` requires a valid `deleteTarget` (a `RegattaDetail` object) and performs a destructive action via the API.

## Gotchas

- **Filter Reset Behavior**: Per commit `36e4547`, the `activeFilter` is automatically cleared if the user changes the `selectedYear` to a year that doesn't contain the current month filter. This prevents "ghost" filters where a user might be looking at a month that doesn't exist in the newly selected year.
- **Date Fallbacks**: The `monthTabs` calculation uses `r.start || r.created`. If a race has a null `start` date, it defaults to the creation timestamp to ensure the race is still bucketed into a visible month/year tab.
- **Empty State/Initial Year**: The `useEffect` for `selectedYear` (lines 78-85) is designed to prevent a blank screen on load. If no races exist, it defaults to the current year; if races exist but not in the current year, it selects the most recent year available from the data.

## Cross-cutting concerns

- **Auth**: Relies on `regattaApi` which requires an authenticated session (admin level).
- **Side effects**: Deleting a race via `handleDelete` triggers a re-fetch of the entire list via `load()`, which updates the UI for the current session.
- **UI/UX**: Uses `useToast` for success/error feedback during the deletion lifecycle.

## External consumers

None known.
