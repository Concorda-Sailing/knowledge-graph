---
node_id: concorda-web::src/components/dashboard/boats-tab.tsx::BoatsList
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6b90ecf44f2467aa653dca1de62bf80fd0ebc4f96f45f6dd00eb91bec5f2ed11
status: llm_drafted
---

# BoatsList

## Purpose

Displays a list of boats associated with the current user, categorized by ownership and crew status. It serves as the primary view for the "Boats" section of the dashboard, providing a high-level overview of a user's fleet and active crew counts. It is distinct from `BoatPage`, which handles the granular detail view of a single selected boat.

## Invariants

- **Data Source**: Fetches data via `profileApi.getMyCrew()`.
- **State Management**: Maintains internal `owned` and `crewed` state arrays to allow for independent updates via WebSocket triggers.
- **Loading State**: Displays a two-column `Skeleton` grid while `loading` is true to prevent layout shift.
- **Empty State**: If both `owned` and `crewed` lists are empty, the component renders an empty container (no explicit empty-state UI is currently implemented).
- **Role-based Visibility**: The "Add Boat" button visibility is controlled by the `canAddBoat` prop, ensuring users without permission do not see the action.

## Gotchas

- **Layout Shift on Desktop**: Per commit `8c8c86c`, the "Add Boat" button was moved to a `hidden md:flex` container to ensure it aligns to the end of the grid on desktop rather than breaking the layout of the boat cards.
- **Crew Count Logic**: The `activeCrewCount` specifically filters for members where `status === "active"` and `role !== "owner"`. This ensures the count reflects active crew rather than the owner or inactive members.
- **WebSocket Refresh**: The component uses `useWsFreshness` to listen for `["boat.updated", "boat_crew.updated"]`. If these events fire, the `load` function is re-executed to ensure the UI reflects recent changes without a manual page refresh.

## Cross-cutting concerns

- **Auth**: Relies on `profileApi.getMyCrew()` which requires a valid session/bearer token.
- **Websocket**: Listens for `boat.updated` and `boat_crew.updated` to trigger a re-fetch of the boat list.
- **Side effects**: Rebuilds the view of the user's fleet when boat or crew metadata changes.

## External consumers

None known.
