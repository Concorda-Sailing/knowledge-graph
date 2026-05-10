---
node_id: concorda-api::schemas/event_crew.py::EventCrewPoolMember
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8b8ea45f5bd4b429e83d990b811612ab6a7819ddccbbe575e6a7aba14a6a3c09
status: current
---

# EventCrewPoolMember

## Purpose

Defines the structure for an individual member within an event's crew pool. It links a `person_uuid` to a specific `role` (e.g., "main" or "alternate") and a `priority` level. This is used to manage the roster of people eligible or assigned to specific positions for an event, distinct from the broader `EventCrewPoolSet` which aggregates these members.

## Invariants

- **`person_uuid` is required.** Every member must be tied to a specific person identifier.
- **`role` defaults to `"main"`.** Valid values are typically `"main"` or `"alternate"`.
- **`priority` is an integer.** It is used to order members within the same role.
- **`position_name` is nullable.** In `EventCrewAssign` and `EventCrewPositionUpdate`, passing `None` acts as an unassign command.

## Gotchas

- **Role/Priority logic is sensitive.** Per commit `dd72f2f`, the `EventCrewStatus` enum and route writes are now the primary way to manage the state of these members; ensure any logic involving `role` or `priority` respects the status transitions.
- **Backward compatibility requirement.** `EventCrewPoolSet` maintains a `person_uuids: list[str]` field alongside the `members` list to support legacy "Simple mode" where only a flat list of IDs was used.

## Cross-cutting concerns

- **Auth**: Subject to standard event-level permissions (e.g., Skipper or Organizer rights) when performing assignments or status updates.
- **Side effects**: Changes to these members impact the visibility of the crew roster in the UI and the `EventCrewStatus` lifecycle.

## External consumers

None known.
