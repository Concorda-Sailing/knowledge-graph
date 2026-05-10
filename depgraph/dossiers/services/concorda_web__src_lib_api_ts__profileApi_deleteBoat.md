---
node_id: concorda-web::src/lib/api.ts::profileApi.deleteBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 78549f28a1da2568f7b3885ceaabd07eab9159c627fe13dd6af8a8fbaf57b099
status: current
---

# profileApi.deleteBoat

## Purpose

The `deleteBoat` method performs a destructive removal of a boat entity from the user's profile. It is used when a user intends to permanently detach a boat from their account. This is a high-stakes operation that should be used sparingly, typically within a confirmation dialog, to prevent accidental loss of boat-scoped data.

## Invariants

- **HTTP Method is `DELETE`** — The request must use the DELETE verb to target the specific boat resource.
- **Requires `fetchApiAuthenticated`** — The call is wrapped in the authenticated fetch helper, requiring a valid bearer token.
- **Returns a success message** — The expected return shape is an object containing a `{ message: string }`.
- **Targeted by ID** — The endpoint is strictly scoped to the specific boat's unique identifier.

## Gotchas

- **Destructive side effects on Crew/Configs** — While this method deletes the boat, ensure the UI handles the cascading implications for boat-scoped objects like `BoatConfig` or `CrewPool`.
- **Dependency on `fetchApiAuthenticated`** — If the authentication layer is modified, this method's ability to reach the `/api/profile/boats/${id}` endpoint may be impacted.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to delete their own boat.
- **Side effects**: Deleting a boat will implicitly affect any UI components relying on the user's boat list, such as `BoatsList` in `src/components/profile/boats-list.tsx`.

## External consumers

- Internal to `concorda-web` (used by `BoatsList` and `BoatInline`).
