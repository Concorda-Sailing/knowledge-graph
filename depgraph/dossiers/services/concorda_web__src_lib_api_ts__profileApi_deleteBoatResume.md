---
node_id: concorda-web::src/lib/api.ts::profileApi.deleteBoatResume
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6bcdf3742d73c3f9cd5f7a95122193e1ec74d361b2f0c8be40edc0bb3c8a3d43
status: llm_drafted
---

# profileApi.deleteBoatResume

## Purpose

Deletes a user's boat resume from their profile. This is a destructive action used to remove a boat's identity/data from the user's profile-scoped resources. It is distinct from `deleteBoatConfig` or `deleteCrewPool`, which manage sub-resources of a boat rather than the primary boat identity itself.

## Invariants

- **HTTP Method is `DELETE`** — Must use the `DELETE` verb to target the specific boat resource.
- **Endpoint Path** — Targets `/api/profile/boats/${boatId}/resume`.
- **Returns a message object** — On success, the API returns `{ message: string }`.
- **Requires Authentication** — Uses `fetchApiAuthenticated` to ensure the user has a valid session and ownership of the resource.

## Gotchas

- **Ownership requirement** — Per commit `47688ac`, operations on boat resources (including deletions) require the user to have Boat Owner membership to prevent unauthorized access or state mutation.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Deleting a boat resume likely impacts any UI components displaying the user's boat list or profile-specific boat details.

## External consumers

None known.
