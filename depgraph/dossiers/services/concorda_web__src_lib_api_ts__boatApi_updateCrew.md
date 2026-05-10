---
node_id: concorda-web::src/lib/api.ts::boatApi.updateCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 89d958fea5925ccf33a468c65c4aee4cdbb28d0e6b4738a946f0709a28f7cb6b
status: current
---

# boatApi.updateCrew

## Purpose

Updates the details of an existing crew member for a specific boat. This method is used to modify attributes like `role`, `position`, `status`, or `notes`. It is distinct from `addCrew` (which creates a new record) and `reorderCrew` (which only changes the sequence of existing members).

## Invariants

- **HTTP Method is `PUT`** — Performs a partial update on the resource.
- **Requires `boatId` and `crewId`** — Both must be provided in the URL path to target the specific member.
- **Returns `BoatCrewMember`** — The response contains the updated state of the member.
- **Payload is partial** — The `data` object allows for optional fields (`role?`, `position?`, etc.), enabling targeted updates without overwriting the entire member object.

## Gotchas

- **Role/Position dependency** — Per commit `bf44b09`, the system now handles `EventCrewStatus` and pool handling; ensure updates to `role` or `position` do not conflict with the logic used for schedule-card pool displays.
- **Config-aware updates** — Per commit `bf15808`, the API relies on `boat_config_id` rather than shape-matching; ensure that updates to the crew member do not inadvertently strip or mismatch the configuration context.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` — requires a valid bearer token.
- **Side effects**: Updates to crew members may affect the visibility of the "accepting-crew" status on regatta detail pages (per commit `2d6b8a7`).

## External consumers

None known.
