---
node_id: concorda-web::src/lib/api.ts::profileApi.transferBoat
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a0501f3fe5f56d8a04bc7e21b17a59ea733348f0073fc2cc64ea89f735f05d8d
status: current
---

# profileApi.transferBoat

## Purpose

Handles the ownership transfer of a boat from the current user to a new owner. This is a specialized administrative action within the profile API that moves the primary ownership record to a different email address. Use this instead of `updateBoat` when the intent is a full change of ownership rather than a metadata update.

## Invariants

- **Method is POST** — specifically targets the `/api/profile/boats/${id}/transfer` endpoint.
- **Requires `new_owner_email`** — the body must contain the string representation of the recipient's email.
- **Returns a success message** — the expected return shape is `{ message: string }`.
- **Uses `fetchApiAuthenticated`** — the caller must be authenticated as the current owner to execute the transfer.

## Gotchas

- **Ownership requirement** — per commit `47688ac`, the system requires the user to have Boat Owner membership to successfully execute ownership-related transitions.
- **Identity dependency** — the transfer relies on the `id` of the boat being the current authenticated user's boat; attempting to transfer a boat not owned by the authenticated user will fail.

## Cross-cutting concerns

- **Auth**: Requires `fetchApiAuthenticated` (authenticated user must be the current owner).
- **Side effects**: Transferring ownership will change the primary owner of the boat, affecting any UI components or permissions tied to the previous owner's profile.

## External consumers

- `concorda-web::src/components/boat/boat-inline.tsx` (via `BoatInline` component).
