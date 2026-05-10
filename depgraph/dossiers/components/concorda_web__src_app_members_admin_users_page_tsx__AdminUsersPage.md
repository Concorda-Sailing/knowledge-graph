---
node_id: concorda-web::src/app/members/admin/users/page.tsx::AdminUsersPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 264b9708942b8a9b7e58fb585ebdb99ef75505a5c9ac2e9aba6e1eb4c55b8220
status: llm_drafted
---

# AdminUsersPage

## Purpose

The central administrative interface for managing organization members. It provides a searchable, paginated table of users and includes controls for creating users, editing profiles, updating passwords, and deleting accounts. It serves as the primary dashboard for administrators to manage the lifecycle of a person within the organization.

## Invariants

- **Uses `adminApi.members` for data fetching.** This method handles the server-side filtering for `search`, `membership_type`, and `year`.
- **`formatJoinDate` uses UTC.** The helper ensures the displayed date matches the date number in the string (e.g., "Jan 1, 2024") regardless of the administrator's local browser timezone.
- **Pagination is fixed at 50.** The `limit` is hardcoded in the `loadUsers` call.
- **Stateful dialogs.** The component manages multiple independent dialog states (`userDialogOpen`, `passwordDialogOpen`, `importDialogOpen`) to control the visibility of administrative actions.

## Gotchas

- **Timezone-sensitive rendering.** Per commit `f444b4c`, all backend datetimes must be rendered in the organization's timezone or UTC to prevent the browser's local time from shifting the displayed day. The `formatJoinDate` helper is a local implementation of this requirement to ensure the date number remains consistent.
- **Mobile layout constraints.** Per commit `0565e0d`, administrative dialogs must maintain specific width caps and footer stacking behaviors to remain functional on smaller screens.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges via `adminApi` (implicitly relies on the session/token established by the auth provider).
- **Side effects**: Changes made here (deletions, password updates, or user creation) directly affect the `adminApi` state and will be reflected in any other admin views or member-facing profile views.

## External consumers

None known.
