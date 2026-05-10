---
node_id: concorda-web::src/app/members/admin/events/socials/page.tsx::SocialsPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7ad999d682381ce469c44aa6cbb681834b02c28fcdf4ba778637a239c3ce45cb
status: llm_drafted
---

# SocialsPage

## Purpose

The administrative management interface for "social" type events. It provides a high-level overview of upcoming social events, displaying registration and ticket counts, and allows administrators to add, import, or delete these events. It serves as the primary dashboard for managing non-competitive social gatherings.

## Invariants

- **Category Filtering**: The component explicitly filters the `adminEventsApi.list()` result set to only include events where `e.category === "social"` or where the category is falsy.
- **Data Aggregation**: Ticket counts and registration counts are derived from `adminTemporalProductsApi.list` and `adminEventsApi.getRegistrationCounts` respectively, and must be re-fetched via `load()` after any deletion.
- **Timezone Consistency**: Uses `formatInOrgTz` with the organization's specific timezone to ensure event dates are rendered correctly for the local audience.
- **Permission Requirement**: Requires the `events.view` permission via the `AdminListPage` wrapper.

## Gotchas

- **Mobile Layout Parity**: Per commit `814cf16`, this page is part of the mobile-optimized admin subpages pattern where tables and card lists are paired. Ensure any UI changes maintain this layout consistency.
- **Import/Add Redirection**: The "Import" and "Add Social Event" buttons rely on specific URL query parameters (`/import-social` and `/new?type=social`) to pre-configure the creation flow; changing these paths breaks the specialized social event creation workflow.

## Cross-cutting concerns

- **Auth**: Requires `events.view` permission via `AdminListPage`.
- **Side effects**: Deleting an event via `adminEventsApi.delete` triggers a re-fetch of the entire dataset (events, tickets, and registration counts) to ensure the UI stays in sync with the server state.

## External consumers

None known.
