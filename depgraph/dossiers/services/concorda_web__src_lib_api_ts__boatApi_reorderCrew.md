---
node_id: concorda-web::src/lib/api.ts::boatApi.reorderCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: aa8df8232056a54c011f9ef86c8daf499576e7cd008aefd8cbed50433e2b92ea
status: llm_drafted
---

# boatApi.reorderCrew

## Purpose

The `reorderCrew` method updates the display order of crew members for a specific boat. It takes an array of person UUIDs and sends them to the `/api/boats/${boatId}/crew/reorder` endpoint via a `PUT` request. This is distinct from `updateCrew`, which modifies individual member attributes like roles or positions; `reorderCrew` is strictly for managing the sequence of the crew list.

## Invariants

- **Method is `PUT`** — The endpoint expects a `PUT` request to update the existing collection order.
- **Payload structure** — The body must be a JSON object containing the key `person_uuids` (an array of strings).
- **Returns the updated list** — The method returns a promise resolving to `BoatCrewMember[]`, representing the new state of the crew order.
- **Requires `boatId`** — The operation is scoped to a specific boat instance.

## Gotchas

- **Ordering is critical for UI consistency** — Per commit `2d6b8a7`, the order of the UUIDs sent here directly affects how the crew is displayed in the "accepting-crew" status and schedule card components.
- **Dependency on `fetchApiAuthenticated`** — Like all methods in this service, this requires a valid authenticated session; it cannot be called from unauthenticated contexts.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires user-level permissions for the boat).
- **Side effects**: Reordering the crew may affect the visual order of members in the `MyCrewTab` component (see `my-crew-tab.tsx:542`).

## External consumers

- `MyCrewTab` in `src/components/dashboard/my-crew-tab.tsx`.
