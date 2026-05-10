---
node_id: concorda-api::schemas/boat.py::BoatCrewInvite
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9aaf5d38e39e6ff47ea649d6bdc8d081bf0ab0957aa21575d86e383e197e9688
status: current
---

# BoatCrewInvite

## Purpose

Defines the schema for inviting a person to join a boat's crew. It is a specialized input model used to initiate a crew relationship, distinct from `BoatCrewUpdate` (which modifies existing relationships) and `BoatCrewRead` (which provides the full state of a relationship). Use this when creating a new invitation record via the API.

## Invariants

- **`person_uuid` is required.** This must be a valid, existing person identifier.
- **`role` defaults to `"crew"`.** While optional in the schema, the logic assumes a standard crew role unless specified otherwise.
- **`config_uuid` is optional.** This allows for attaching specific configuration contexts to the invite.
- **Input is a Pydantic model.** It is used as the request body for the `POST /api/boats/{boat_uuid}/crew/invite` endpoint.

## Gotchas

- **Implicit role assignment.** Because `role` defaults to `"crew"`, automated scripts or manual API calls that omit the role field will unintentionally assign the standard crew role.
- **Dependency on `person_uuid` existence.** The API expects a valid person to be linked; failure to provide a valid UUID results in a 400/422 error at the router level.

## Cross-cutting concerns

- **Auth**: Requires authenticated access to the boat resource via the `POST /api/boats/{boat_uuid}/crew/invite` router.
- **Side effects**: Successful creation of this model via the router triggers the creation of a new crew record, which will eventually be visible in `BoatCrewRead` views.

## External consumers

- `POST::/api/boats/{0}/crew/invite` (via `routers/boats.py:556`)
