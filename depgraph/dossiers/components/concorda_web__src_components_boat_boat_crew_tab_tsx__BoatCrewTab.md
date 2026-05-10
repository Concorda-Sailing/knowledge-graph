---
node_id: concorda-web::src/components/boat/boat-crew-tab.tsx::BoatCrewTab
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0fe52007a962f8c09068f781668440d4f17381e7bc6df26fc6b9be60ab2c98da
status: current
---

# BoatCrewTab

## Purpose

Displays a list of visible crew members for a specific boat. It fetches and renders user avatars, names, and roles (e.g., "owner" or specific positions) as clickable links to their profiles. This component is used within the boat detail view to show who is currently associated with the vessel.

## Invariants

- **Requires `boatId`** — The component cannot function without a valid string ID to fetch the crew list.
- **Sort order is strict** — The list must always place the "owner" at the top, followed by alphabetical sorting by `first_name`.
- **Returns empty state** — If the API call fails or the crew list is empty, it renders a specific empty-state UI (a centered icon and message) rather than a blank space.
- **Uses `boatApi.getVisibleCrew`** — Data is fetched via this specific method to ensure only members with public/visible profiles are displayed.

## Gotchas

- **Manual sorting logic** — The component performs its own client-side sort on the `data` array. If the API contract for `role` or `first_name` changes, the visual order of the crew list will break.
- **Skeleton state** — While `crew` is `null` (initial load), it renders a row of `Skeleton` components to prevent layout shift.

## Cross-cutting concerns

- **Auth**: Relies on `boatApi.getVisibleCrew` which requires an authenticated session to view boat-specific crew data.
- **Websocket**: Listens to the `boat_crew.updated` event via `useWsFreshness` to trigger an automatic refetch when the crew list changes.
- **Side effects**: Re-renders the crew list automatically when the boat's crew membership is updated via websocket.

## External consumers

None known.
