---
node_id: concorda-web::src/components/dashboard/boats-tab.tsx::BoatsTab
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 81ce3faf6a3f26caf3b72b6f1794156ecb18c618f5309bd93d0588509b8a8966
status: current
---

# BoatsTab

## Purpose

The `BoatsTab` component manages the display of a user's fleet within the dashboard. It acts as a router-lite, checking `searchParams` for a `boat` ID to decide whether to render the `BoatsList` (the overview) or an inline `BoatPage` (the detail view). This allows users to drill into a specific boat's details without losing their dashboard navigation context.

## Invariants

- **Inline Detail Routing**: If `searchParams.get("boat")` is present, the component renders `BoatPage` instead of the list.
- **Data Fetching**: Uses `profileApi.getMyCrew()` to populate the list; failure to fetch results in an empty state (`[]`) rather than an error state.
- **Permission-based UI**: The "Add Boat" button visibility is strictly controlled by the `canAddBoat` prop, which is derived from user membership permissions.
- **State Management**: The `BoatsList` sub-component maintains its own loading and data state, fetching data on mount via `useEffect`.

## Gotchas

- **Inline Navigation UX**: Per commit `a29494e`, the boat detail is now inlined. If you change the routing logic to a full-page navigation, you will break the "Back to Boats" link behavior and the user's navigation context.
- **Desktop Layout Shifts**: Per commit `fb280b3`, the "Add Boat" button is hoisted to the top on desktop and paired with the crew tab. Ensure any changes to the `canAddBoat` logic or button placement respect the `hidden md:flex` styling to avoid breaking the desktop layout.
- **Real-time Sync**: The component relies on `useWsFreshness` for the `boat.updated` and `boat_crew.updated` events. If these event names are changed in the backend or the hook, the list will not auto-refresh when a boat's details change.

## Cross-cutting concerns

- **Auth**: Requires membership permissions to trigger `onAdd-Boat` (via `canAddBoat`).
- **Websocket**: Listens to `boat.updated` and `boat_crew.updated` via `useWsFreshness` to trigger a re-fetch of `getMyCrew`.
- **Side effects**: Rebuilds the `BoatsList` view when the `boat` search parameter changes.

## External consumers

None known.
