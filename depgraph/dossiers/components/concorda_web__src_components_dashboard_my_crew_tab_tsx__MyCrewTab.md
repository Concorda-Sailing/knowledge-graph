---
node_id: concorda-web::src/components/dashboard/my-crew-tab.tsx::MyCrewTab
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f816954beb5137b3a5f07953daf650b3ab30cbd4b7f5a881a3dd84288a27bdd6
status: current
---

# MyCrewTab

## Purpose

The `MyCrewTab` component displays a user's personal crew information, including their roles within specific boats and their associated "Crew Pools." It provides administrative controls for managing these relationships, such as creating/deleting pools and removing members. It is distinct from the `AvailableSection` or `CrewPositionsCard` in that it is a high-level dashboard view focused on the user's own identity and boat-scoped group management rather than general race-day logistics.

## Invariants

- **Boat-scoped grouping** — Crew pools are tied to a specific `boatId`. Operations like `createCrewPool` or `deleteCrewPool` must include the current boat's ID to satisfy the API contract.
- **Role-based permissions** — The `onRemove` handler is only passed to members if their role is not `"owner"`.
- **Data fetching lifecycle** — The component uses `fetchData` inside a `useEffect` to populate `data` (user profile) and `poolsByBoat` (the mapping of boat IDs to their respective `CrewPool[]`).
- **State-driven UI** — UI elements like `removingIds` and `resendingId` are used to track optimistic or pending async operations to prevent multiple concurrent clicks on the same action.

## Gotchas

- **Pool scoping requirement** — Per commit `2e089b2`, crew pools are now strictly scoped to a boat. Attempting to manage pools without the correct `boatId` context will fail.
- **Display logic regression** — A recent revert in commit `d4f19bb` (and the preceding `b9c490d`) highlights a sensitivity in how pools are displayed. The logic was adjusted to ensure person-owned pools are shown per-boat rather than once globally, to avoid ambiguity in the UI.
- **Async error handling** — The component uses `toast` to surface errors from `profileApi`. If a `fetchData` call fails, the component sets `data` to `null` and sets `loading` to `false` to prevent infinite loading states.

## Cross-cutting concerns

- **Auth**: Uses `profileApi` which requires an authenticated session (bearer token).
- **Side effects**: Rebuilding the `data` state via `fetchData()` is required after any mutation (e.g., `handleCreateGroup`, `handleDeleteGroup`) to ensure the UI reflects the new state of the backend.

## External consumers

None known.

## Open questions

- The `onRemove` logic in the source (line 106) checks `member.role !== "owner"`, but the component doesn't explicitly define how "owner" status is derived from the `profileApi` response if the user is the one viewing the tab.
