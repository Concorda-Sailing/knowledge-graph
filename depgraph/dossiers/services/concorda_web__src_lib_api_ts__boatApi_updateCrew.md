---
node_id: concorda-web::src/lib/api.ts::boatApi.updateCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 89d958fea5925ccf33a468c65c4aee4cdbb28d0e6b4738a946f0709a28f7cb6b
status: llm_drafted
---

# boatApi.updateCrew

## Purpose
`boatApi.updateCrew` is a specialized service method used to modify the attributes of an existing crew member within a specific boat. It is distinct from `addCrew` (which creates a new entry) and `reorderCrew` (which only modifies the sequence of members). A future agent should reach for this function when a user needs to update non-structural metadata like a person's `role`, `position`, `status`, or `notes`.

## Invariants
* Performs a `PUT` request to `/api/boats/${boatId}/crew/${crewId}`.
* Requires an authenticated session via `fetchApiAuthenticated`.
* Returns a `BoatCrewMember` object on success.
* The `boatId` and `crewId` must be valid identifiers for the target boat and crew member respectively.

## Gotchas
* **Partial Updates**: The function accepts an object with optional fields (`role`, `position`, `config_uuid`, `status`, `notes`), implying a partial update pattern; however, ensure the backend handles missing keys as "no change" rather than nulling them out.
* **Configuration Sensitivity**: Recent changes (commit `bf15808`) suggest that `boat_config_id` is a critical piece of data; ensure that updates involving configuration-aware fields are handled carefully to avoid breaking the `config-aware count` logic on schedule cards.

## Cross-cutting concerns
* **State Synchronization**: Updates to crew members (especially `status` or `role`) may affect the display of "Accepting-Crew" badges or "Looking for a ride" status on regatta detail views and schedule cards.
* **Auth**: Requires valid user authentication to modify boat-specific crew data.

## External consumers
* `concorda-web::src/components/boat/boat-crew-table.tsx` (BoatCrewTable)
* `concorda-web::src/components/dashboard/my-crew-tab.tsx` (MyCrewTab)

## Open questions
* None.
