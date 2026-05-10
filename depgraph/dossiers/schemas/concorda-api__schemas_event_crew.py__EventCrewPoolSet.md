---
node_id: concorda-api::schemas/event_crew.py::EventCrewPoolSet
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e758e5cc5a588b81b89c298aa4bee25f4ee923a4a96468d2e9ecf7578cf503ba
status: llm_drafted
---

# EventCrewPoolSet

## Purpose

Defines the data structure for a set of people assigned to a specific event's crew pool. It supports two modes of operation: a "Simple mode" using a flat list of `person_uuids` for backward compatibility, and a "Rich mode" using the `members` list (via `EventCrewPoolMember`) to track specific roles and priorities. Use this schema when updating the roster via the `PUT /api/events/{0}/sailing-event/crew-pool` endpoint.

## Invariants

- **Dual-mode compatibility**: The schema allows both `person_uuids` (flat list) and `members` (structured list) to coexist for backward compatibility.
- **Role defaults to "main"**: If a `role` is not explicitly provided in an `EventCrewPoolMember`, it defaults to `"main"`.
- **Priority is integer-based**: The `priority` field in `EventCrewPoolMember` is an integer, used to order the crew list.

## Gotchas

- **Backward compatibility requirement**: The existence of both `person_uuids` and `members` is a requirement for the transition from the legacy flat-list system to the new structured role system.
- **Role/Priority dependency**: When using "Rich mode," the `role` and `priority` fields are critical for the UI to correctly display the hierarchy of the crew (e.g., distinguishing between main crew and alternates).

## Cross-cutting concerns

- **Auth**: Managed by the `PUT /api/events/{0}/sailing-event/crew-pool` router; requires appropriate event-level permissions.
- **Side effects**: Updates to this schema via the crew-pool endpoint trigger updates to the boat-finder count and the event's roster display.

## External consumers

- `PUT /api/events/{0}/sailing-event/crew-pool` (routers/events.py:2413)

## Open questions

- Should the API enforce a rule that `person_uuids` must be empty if `members` is populated to prevent ambiguity in the "Simple" vs "Rich" mode?
