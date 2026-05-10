---
node_id: concorda-web::src/components/boat/boat-crew-view.tsx::BoatCrewView
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8cb5e9186b3e69e9d095879e57afb3041de2d5594955496023e2d51fffedea0e
status: current
---

# BoatCrewView

## Purpose

The primary view for a boat's identity and personnel, orchestrating the display of high-level boat details, the crew list, and media. It acts as a container that fetches and synchronizes both `BoatDetail` and `BoatResume` data via `boatApi`. Use this component when you need a comprehensive dashboard for a specific boat, rather than just a single tab or a simplified header.

## Invariants

- **Requires a valid `boatId`** to initiate data fetching.
- **Fetches two distinct data sources in parallel** via `Promise.allSettled`: `boatApi.getDetail(boatId)` and `boatApi.getResume(boatId)`.
- **Uses `useWsFreshness`** to trigger a full re-fetch of both detail and resume data when specific boat-related events occur.
- **Displays a loading skeleton** until both API calls have settled and the `loading` state is set to `false`.

## Gotchas

- **Error handling for detail fetch failures:** Per commit `fac0fdb`, the component must explicitly handle the case where `boatApi.getDetail` fails to ensure the user sees an error state rather than an infinite loading spinner or a broken UI.
- **Race conditions in refetching:** The `refetch` function uses `Promise.allSettled` to ensure that a failure in fetching the `resume` does not prevent the `boat` detail from being displayed.

## Cross-cutting concerns

- **Auth**: Implicitly relies on `boatApi` which requires an authenticated session to fetch boat details.
- **Websocket**: Listens to and reacts to `"boat.updated"` and `"boat_crew.updated"` events to trigger a component-level re-fetch.
- **Side effects**: Re-renders the entire view (including `BoatProfileTab` and `BoatCrewTab`) when the boat or crew data is updated via the websocket.

## External consumers

None known.
