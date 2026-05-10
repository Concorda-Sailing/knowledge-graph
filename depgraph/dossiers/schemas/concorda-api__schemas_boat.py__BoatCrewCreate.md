---
node_id: concorda-api::schemas/boat.py::BoatCrewCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 248567b413ccf4776e5ee616d61218625384e67b09e2b0f645f58874a33ccf26
status: llm_drafted
---

# BoatCrewCreate

## Purpose

The input schema for creating a new crew member association on a boat. It defines the required identity (`person_uuid`) and the initial role-based configuration. This is distinct from `BoatCrewInvite`, which is used for the invitation flow, and `BoatCrewUpdate`, which allows for modifying existing crew members.

## Invariants

- **`person_uuid` is required.** It must be a valid UUID string representing a person in the system.
- **`role` defaults to `"crew"`.** Valid options are `owner`, `crew`, or `prospective`.
- **`position` and `config_uuid` are optional.** These allow for specialized roles or configuration-driven assignments.
- **Used by `POST /api/boats/{0}/crew`** to establish the initial relationship between a person and a boat.

## Gotchas

- **Role assignment is sensitive to the creation flow.** Per commit `68a7508` (migrations 048–056), this schema is part of the refined crew roster service; ensure that the `role` provided matches the expected lifecycle of a new crew member to avoid downstream errors in the roster service.

## Cross-cutting concerns

- **Auth**: Handled by the `POST /api/boats/{0}/crew` endpoint (requires authenticated owner/admin permissions).
- **Side effects**: Creation of a crew member via this schema triggers updates to the boat's roster visibility.

## External consumers

- `POST /api/boats/{0}/crew` (internal API router).
