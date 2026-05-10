---
node_id: concorda-web::src/lib/api.ts::crewfinderApi.getCrewDetail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5609a34ad4524e0bfd2f40a4ebb58146c836e0b0d5190060f80b97469b05ec8c
status: current
---

# crewfinderApi.getCrewDetail

## Purpose

Fetches the full profile details for a specific person via the Crewfinder service. It is used to populate detailed views for individuals within the directory. Use this method when you need the `CrewfinderProfileDetail` object, rather than the lighter `getBoatDetail` or the broader `searchBoats` methods.

## Invariants

- **Requires `personId`** — The input must be a valid, URL-encoded string representing the person's unique identifier.
- **Uses `fetchApiAuthenticated`** — The request is subject to the same authentication and bearer token requirements as the rest of the `api.ts` service.
- **Returns `CrewfinderProfileDetail`** — The response shape is strictly tied to the profile detail schema.

## Gotchas

- **Recent decoupling of schedule data** — Per commit `1b5d864`, the detail view logic was updated to ensure it doesn't inadvertently couple to `mySchedule` data, which was a previous source of friction in detail page rendering.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to view directory details.
- **Side effects**: Data returned here is used to populate the `CrewDetailPage` in the members directory.

## External consumers

- `concorda-web::src/app/members/crewfinder/crew/[id]/page.tsx::CrewDetailPage`
