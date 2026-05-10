---
node_id: concorda-web::src/lib/api.ts::boatApi.getResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: eca735267c04fa1f0f24a9a840dfaccec3e405076bb325897c962f114454b19b
status: current
---

# boatApi.getResume

## Purpose

Fetches the high-level summary data for a specific boat. It is used to populate lightweight "resume" views where a full `getDetail` or `getVisibleCrew` call would be too heavy or provide unnecessary information. Use this when you need a quick snapshot of a boat's status without the overhead of full member or event lists.

## Invariants

- **HTTP Method**: `GET`
- **Endpoint**: `/api/boats/${boatId}/resume`
- **Auth**: Requires a valid session via `fetchApiAuthenticated`.
- **Return Shape**: Returns a `BoatResume` object.

## Gotchas

- **Data-driven UI updates**: Per commit `2d9e4c8` (implied by `feat(crew): show accepting-crew status...`), the data returned here is used to drive status badges (like "Accepting-Crew") on the regatta detail and schedule cards. Changes to the shape of `BoatResume` can break the visual state of these high-level components.
- **Dependency on `boatId`**: The function relies on a valid `boatId` string; if the ID is malformed or missing, `fetchApiAuthenticated` will trigger a 401 or 404 depending on the auth state.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to view the boat's summary.
- **Side effects**: The data returned is consumed by the `BoatCrewView` and `BoatInviteView` to display high-level boat status/identity.

## External consumers

None known.
