---
node_id: concorda-web::src/app/members/crewfinder/boat/[id]/page.tsx::BoatDetailPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ea1483306a39396467ff140e4be91002f4fa6698b4db98758ce85962ae306bc8
status: llm_drafted
---

# BoatDetailPage

## Purpose

Renders the detailed profile view for a specific boat within the Crewfinder module. It fetches and displays boat-specific metadata (class, manufacturer, length, sail number) and visual assets (banner and avatar) via the `crewfinderApi`. This page serves as the primary landing point for users viewing a boat's identity and is distinct from the list-view components that aggregate multiple boats.

## Invariants

- **Requires a valid `id` parameter** from the URL to fetch the specific profile.
- **Uses `crewfinderApi.getBoatDetail(boatId)`** to retrieve the `BoatCrewfinderProfileDetail` object.
- **Displays a fallback UI** (Skeleton) during the loading state and a "Boat not found" error state if the API call fails or returns no data.
- **The `HeroBanner` title is polymorphic**: it defaults to `profile.boat_name` but falls back to `profile.sail_number` if the name is missing.
- **The `isOwnBoat` check** relies on the `useBoats` hook to determine if the current user is the owner of the boat being viewed.

## Gotchas

- **Permission Gate requirement**: The entire view is wrapped in a `<PermissionGate permission="crewfinder.view">`. If the user lacks this specific permission, the component will render nothing or the gate's fallback, even if the API call succeeds.
- **Identity mismatch in `isOwnBoat`**: The logic `boats.some((b) => b.id === boatId)` assumes the `useBoats` hook returns a list that includes the current boat's ID. If the list is filtered by the backend, this check may fail even if the user owns the boat.

## Cross-cutting concerns

- **Auth**: Wrapped in `<PermissionGate permission="crewfinder.view">`.
- **Side effects**: The `isOwnBoat` state is derived from `useBoats`, meaning changes to the user's boat list (e.g., via a different component) will update the ownership context here.

## External consumers

None known.
