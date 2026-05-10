---
node_id: concorda-web::src/lib/api.ts::boatApi.getVisibleCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 44f9b1d604b74925b9048c1ebd0199842f693b62d5afe058ffc3fc49cc65c9dc
status: llm_drafted
---

# boatApi.getVisibleCrew

## Purpose

Fetches the list of crew members visible to the current user for a specific boat. This is a read-only view used to populate UI components that display personnel associated with a vessel, such as the `BoatCrewTab`. It is distinct from administrative or co-owner-specific endpoints as it returns a filtered `VisibleCrewMember[]` array based on the user's current visibility permissions.

## Invariants

- **Method is `GET`** via `fetchApiAuthenticated`.
- **Requires `boatId`** as a string path parameter.
- **Returns `VisibleCrewMember[]`**, an array of objects representing the visible crew members.
- **Requires authentication** via the `fetchApiAuthenticated` wrapper.

## Gotchas

- **Visibility is context-dependent.** Per commit `2d6b8a7`, the crew list is used to drive the "accepting-crew" status on regatta detail pages and schedule cards. Changes to the visibility logic in the backend will directly impact how many people appear in these UI elements.
- **Relationship to `BoatCrewTab`.** This method is the primary data source for `concorda-web::src/components/boat/boat-crew-tab.tsx`.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to view the boat's crew.
- **Side effects**: The data returned by this method populates the `BoatCrewTab` and influences the "accepting-crew" badge visibility on the regatta detail page.

## External consumers

None known.
