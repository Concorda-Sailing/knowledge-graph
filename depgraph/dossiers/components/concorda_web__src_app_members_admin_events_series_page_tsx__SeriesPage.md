---
node_id: concorda-web::src/app/members/admin/events/series/page.tsx::SeriesPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1b0f50eafe332904a37bd9cc447ecde5b7d297fbaaff64db7371bb5feaa5f9ff
status: llm_drafted
---

# SeriesPage

## Purpose

The administrative management interface for race series. It provides a searchable, filterable list of existing series and allows administrators to create or edit them via a dialog-driven workflow. It serves as the primary control plane for organizing multiple races into a cohesive series structure.

## Invariants

- **Permission requirement**: The component is wrapped in `AdminListPage` with the `events.view` permission requirement.
- **Data fetching**: Uses `seriesApi.list()` to populate the view; the list is refreshed via the `load()` function after any mutation (delete/edit).
- **Date rendering**: Uses `formatInOrgTz` with a specific short format (`month: "short", day: "numeric", year: "numeric"`) to ensure consistency with the organization's local time.
- **Filter state**: Filters for `qualifiers` and `scoring_system` are maintained as `Set<string>` to allow for multiple simultaneous selections.

## Gotchas

- **Mobile layout constraints**: Per commit `0564f06`, admin dialogs must cap their width and ensure the footer stacks on small screens to prevent UI breakage on mobile devices.
- **Mobile grid reflow**: Per commit `019f6e3`, the admin subpages (including this one) require a blanket single-column form reflow to remain usable on mobile-sized viewports.
- **Search/Filter interaction**: The `filtered` memo relies on a case-insensitive search of both `name` and `location`. If a series lacks a name or location, the search logic must handle the empty string gracefully to avoid runtime errors.

## Cross-cutting concerns

- **Auth**: Requires `events.view` permission via `AdminListPage`.
- **Side effects**: Mutations here (add/edit/delete) directly affect the data used by the sailing calendar and race-finder components.

## External consumers

None known.

## Open questions

- The `availableQualifiers` and `availableScoring` are derived from the current `seriesList`. If the API adds new types, they will appear automatically, but there is no mechanism here to manage a master list of valid options.
