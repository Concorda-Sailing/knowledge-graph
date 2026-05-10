---
node_id: concorda-api::schemas/boat.py::BoatCrewUpdate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 07078a6b680763b713b072434e4d0e19c4cd2f3219722cb72db72c6b3483072d
status: current
---

# BoatCrewUpdate

## Purpose

The schema for updating an existing crew member's relationship to a boat. It is used by the `PUT /api/boats/{boat_uuid}/crew/{person_uuid}` endpoint to allow modification of roles, positions, or status without requiring the `person_uuid` or `boat_uuid` to be passed in the body. It is distinct from `BoatCrewCreate` and `BoatCrewInvite`, which require identity identifiers, whereas this is strictly for partial updates to an existing record.

## Invariants

- **All fields are optional.** The model is designed for partial updates (PATCH-style behavior via PUT), allowing a caller to update only the `role`, `status`, or `notes`.
- **Does not include identity fields.** Unlike `BoatCrewCreate`, this schema does not contain `person_uuid` or `boat_uuid`; these are derived from the URL path parameters.
- **`role` is a string.** While the documentation implies specific roles (owner, crew, prospective), the schema itself treats it as a standard string.

## Gotchas

- **Part of the "crew roster service" refinement.** Per commit `68a7508`, this schema is part of the recent refactor to stabilize the crew management logic and router-level refinements.

## Cross-cutting concerns

- **Auth**: Dependent on the boat-level authorization logic in the `routers/boats.py` router.
- **Side effects**: Updates to this schema (specifically `role` or `status`) may trigger changes in how a user's permissions are perceived by the boat's management layer.

## External consumers

- `PUT /api/boats/{boat_uuid}/crew/{person_uuid}` in `routers/boats.py`.
