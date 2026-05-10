---
node_id: concorda-api::schemas/regatta.py::MatchRoster
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 26a2e7cfcf64331f2aa76f19303f91a54dcb8a52a5dd676f8380be35ea6dd3f8
status: current
---

# MatchRoster

## Purpose

The `MatchRoster` schema defines the structure for a regatta's current participation state, aggregating both boat and crew data. It is used to provide a snapshot of who is participating in a specific regatta, distinguishing between the physical vessels (`RosterBoat`) and the human participants (`RosterCrew`). An agent should use this schema when building or modifying endpoints that need to display the "who's who" of a regatta, such as the match-roster view.

## Invariants

- **Compositional structure**: The model must contain a `boats` list of type `RosterBoat` and a `crew` list of type `RosterCrew`.
- **Default initialization**: Both `boats` and `crew` default to empty lists (`[]`) if not explicitly provided, preventing null-pointer errors in the frontend.
- **Strict typing**: The schema relies on the underlying `RosterBoat` and `RosterCrew` definitions; changes to those sibling models will propagate here.

## Gotchas

- **Per commit `6c9b5f3`**, there is a subtle distinction between the "on-calendar" state and the "accepting-crew" state. A per-race toggle can drive the `Accepting-Crew` status, which affects how the roster is displayed. If a user is looking at the roster, they might see all boats currently on the calendar, even if they aren't part of the active "accepting" flow.
- **The relationship between boats and crew is implicit**: The schema does not explicitly link a `RosterCrew` member to a specific `RosterBoat` via an ID in this model, relying on the backend to maintain that association in the database.

## Cross-cutting concerns

- **Auth**: Dependent on the regatta-specific access controls (likely handled by the router `GET /api/regattas/{0}/match-roster`).
- **Side effects**: Changes to the roster state (adding/removing boats or crew) directly impact the visibility of the regatta's participation density in the UI.

## External consumers

- `GET /api/regattas/{0}/match-roster` (Direct consumer via `routers/regattas.py`).
