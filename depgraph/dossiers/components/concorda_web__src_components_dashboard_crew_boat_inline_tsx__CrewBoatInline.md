---
node_id: concorda-web::src/components/dashboard/crew-boat-inline.tsx::CrewBoatInline
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ffa5f9ecc9ebc6fcf46ecccb1863325acb030166d59253dd5eb80729d50c2dcf
status: current
---

# CrewBoatInline

## Purpose

The `CrewBoatInline` component provides a high-density summary of a boat's identity, including its name, sail number, banner image, and current crew/punchlist status. It is designed to be an embedded "hero" section for various dashboard views (like boat finder or profile pages) rather than a full-page layout. Use this when you need a self-contained, data-rich snapshot of a boat that stays in sync with real-time updates.

## Invariants

- **Requires a valid `boatId`** to initiate all data fetching.
- **Fetches three distinct datasets in parallel** via `Promise.all`: boat details, crew members, and the punchlist.
- **Uses `useWsFreshness`** to trigger a re-fetch of all three data streams when specific events occur.
- **Displays a fallback gradient** if `boat.banner_url` is missing or fails to load.
- **Displays `boat.name` as the primary heading**, falling back to `boat.sail_number` if the name is null.

## Gotchas

- **Race conditions in `fetchData`**: The component relies on `useCallback` and `useEffect` to manage the lifecycle of three concurrent API calls. If the `boatId` changes rapidly, the `setBoat`/`setCrew`/`setPunchlist` calls might resolve in an unexpected order, though the `loading` state guards the initial render.
- **Silent failure on API error**: Per the `try/catch` blocks in `fetchData` and `refreshPunchlist`, errors in the `boatApi` calls (e.g., 404 or 500) result in the component silently retaining its default empty states (empty arrays/null) rather than throwing an error to the parent.

## Cross-cutting concerns

- **Auth**: Uses `useAuth()` to establish context, though the component's primary data fetching is driven by the `boatId`.
- **Websocket**: Listens for and reacts to `"boat.updated"` and `"boat_crew.updated"` via `useWsFreshness`.
- **Side effects**: Recent commit `7ca64bf` indicates this is used as a primary visual element in the **boat finder**, **crew finder**, and **profile pages**.

## External consumers

None known.
