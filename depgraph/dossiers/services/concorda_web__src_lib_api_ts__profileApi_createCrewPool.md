---
node_id: concorda-web::src/lib/api.ts::profileApi.createCrewPool
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fda9c4c66d01f5f8a1536e64e3233292636ad5f361dc7e4d2eb60cd142bc8c2a
status: llm_drafted
---

# profileApi.createCrewPool

## Purpose

Creates a new crew pool under a specific boat's scope. This method is used to group members together for organized participation in events. It is distinct from `listCrewPools` (which retrieves existing pools) and `updateCrewPool` (which modifies them), serving as the primary entry point for establishing new group identities within a boat's configuration.

## Invariants

- **Method is `POST`** — Sends a request to `/api/profile/boats/${boatId}/crew-pools`.
- **Requires `boatId`** — The creation is strictly scoped to the provided boat identifier.
- **Payload structure** — Expects a `data` object containing a `name` (string) and `member_ids` (array of strings).
- **Returns `CrewPool`** — On success, returns the newly created pool object.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to establish the session.

## Gotchas

- **Recent structural changes** — Per commit `bf15808`, the API logic is sensitive to the relationship between boat configurations and crew; ensure the `boatId` passed is the correct identifier for the boat context being edited.
- **Type-driven UI** — Per commit `bf44b0b`, the `EventCrewStatus` type union and schedule-card pool handling are tightly coupled to how these pools are surfaced in the UI.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires valid user session).
- **Side effects**: Rebuilds/updates the `MyCrewTab` component in the dashboard.

## External consumers

- `MyCrewTab` component in `src/components/dashboard/my-crew-tab.tsx`.
