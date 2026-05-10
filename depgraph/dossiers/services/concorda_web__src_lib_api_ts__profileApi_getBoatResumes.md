---
node_id: concorda-web::src/lib/api.ts::profileApi.getBoatResumes
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8eb5541ef3762894263c2d6b7931cb7a3d04c907b94693fa5abcb188eb9e106f
status: llm_drafted
---

# profileApi.getBoatResumes

## Purpose

Retrieves the full list of `BoatResume` objects associated with the authenticated user's profile. This is the primary method for fetching the user's personal "fleet" overview. Use this when a view needs to list all boats the user manages, rather than a specific single boat's details (which uses `getBoatResume`).

## Invariants

- **Returns an array of `BoatResume` objects.** If the user has no boats, it returns an empty array `[]`, not `null`.
- **Requires authentication.** Uses `fetchApiAuthenticated` to ensure the request includes the bearer token.
- **Endpoint is a GET request.** The underlying path is `/api/profile/boat-resumes`.

## Gotchas

- **Relationship to `getBoatResume` (singular).** While this returns the list, individual boat details or updates (like `updateBoatConfig`) require a specific `boatId`.
- **Recent schema changes.** Per commit `bf44b09`, the relationship between boat resumes and crew status is becoming more complex; ensure that any UI consuming this list is prepared for the `EventCrewStatus` type union if it intends to display status indicators alongside the boat list.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: The result of this call is used to populate the user's boat list in the dashboard and profile views.

## External consumers

None known.
