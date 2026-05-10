---
node_id: concorda-api::schemas/regatta.py::RosterBoat
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 62fb829117d2548ab87128fe0414cbeb8a6f2fe47ffbe28f539bd06dd387faee
status: current
---

# RosterBoat

## Purpose

Represents the state of a specific vessel within a regatta or event roster. It bridges the gap between a static `Boat` entity and a dynamic `SailingEvent` by tracking real-time participation metrics like available positions and crew request status. Use this model when you need to display the "live" status of a boat's availability to users during a race.

## Invariants

- **`boat_id` and `event_id` are required strings** to maintain the relational link between the vessel and the specific regatta instance.
- **`accept_crew_requests` is a per-race toggle**; it determines if the boat is currently open to incoming crew requests for this specific event.
- **`slots` represents the denominator** for capacity; it is the total number of positions needed on the `SailingEvent` (defaults to 0).
- **`accepted_count` tracks active status**; it is the count of crew members with `status='accepted'` currently assigned to this boat.

## Gotchas

- **The `accept_crew_requests` toggle is race-specific.** Per commit `6c9b5f3`, this toggle drives the "Accepting-Crew" UI state and ensures the list shows all boats currently on the calendar.
- **`slots` vs `accepted_count` logic.** Per commit `fdc87b4`, the `slots` field is the denominator used to calculate the remaining capacity/availability for the event.
- **`match_counts` is transient.** As noted in the `RosterBoat` class definition, `match_counts` is a field populated by specific list/get endpoints and should not be expected to persist through a standard `POST` or `PUT` update.

## Cross-cutting concerns

- **Auth**: None (this is a schema-only definition).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Drives the "Accepting-Crew" visibility in the calendar view and influences the "Boat Finder" availability logic.

## External consumers

None known.

## Open questions

- Should the `accept_crew_requests` logic be moved to the `SailingEvent` level entirely, or is the per-boat/per-race granularity intentional for complex regatta workflows?
