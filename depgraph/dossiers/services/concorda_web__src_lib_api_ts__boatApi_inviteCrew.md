---
node_id: concorda-web::src/lib/api.ts::boatApi.inviteCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a4465406ad3c5aa8c85298d2d8597ebc46c7225b87418ee90a469b733c912534
status: llm_drafted
---

# boatApi.inviteCrew

## Purpose

Sends a POST request to invite a specific person to join a boat's crew. It is used to transition a person from a "directory" contact to an active crew member with a specific role and position. Use this for single-user invites; for bulk-inviting via email, use `inviteCrewBatch` instead.

## Invariants

- **HTTP Method**: `POST`.
- **Endpoint**: `/api/boats/${boatId}/crew/invite`.
- **Auth**: Requires a valid bearer token via `fetchApiAuthenticated`.
- **Payload Shape**: Requires `person_uuid`. `role`, `position`, and `config_uuid` are optional but can be provided to pre-configure the membership.
- **Return Type**: Returns the newly created `BoatCrewMember` object.

## Gotchas

- **Role/Position dependency**: Per commit `bf44b09`, the `EventCrewStatus` type union and schedule-card pool handling are sensitive to how roles are assigned. Ensure the `role` and `position` strings align with the updated schema to avoid breaking the "looking for a ride" status or schedule card displays.
- **Co-owner distinction**: Do not use this for co-owner invites. `coownerInvite` is a separate endpoint with a different payload structure (accepting either `person_uuid` or `email`).

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires authenticated session).
- **Side effects**: Inviting a crew member may trigger updates to the "accepting-crew" status and the "looking for a ride" badge on regatta/schedule detail pages (per commit `2d6b8a7`).

## External consumers

- `CrewDetailPage` (via `page.tsx:64`)
- `BoatCrewInvite` component (via `boat-crew-invite.tsx:188`)
