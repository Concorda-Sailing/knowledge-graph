---
node_id: concorda-api::services/match_counts.py::compute_match_counts
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 06f3e08cd9e88edc0e6ce8aaa6cdeffd5e933f8a5b99451bebe4a429a1c756a4
status: current
---

# compute_match_counts

## Purpose

Calculates real-time availability metrics for a list of regattas, specifically focusing on boat presence and crew availability. It provides the data used to drive the "looking for crew" status and the count of available crew members. This is distinct from `get_match_roster`, which returns the actual lists of people; this function is purely for the high-level numeric signals used in UI badges and summaries.

## Invariants

- **Input is a list of `regatta_ids`**; if the list is empty, returns an empty dictionary.
- **Returns a dictionary keyed by `regatta_id`** with a nested structure: `{regatta_id: {boats_total, boats_looking, crew_available}}`.
- **`boats_looking` is driven by the per-race toggle**, not the boat-level setting. A boat is "looking" only if the specific `SailingEvent` has `accept_crew_requests` set to true.
- **`crew_available` excludes captains and matched crew.** A person is removed from the available count if they have an `accepted` status on any `SailingEvent` within the provided regatta.
- **Role inference fallback:** If `PersonEvent.role` is `NULL`, the system infers "captain" if the person owns a boat with a `SailingEvent` on this regatta, otherwise "crew".

## Gotchas

- **The "Looking" signal is per-race, not per-boat.** Per commit `6c9b5f3`, the `SailingEvent.accept_crew_requests` toggle drives the "Accepting-Crew" status. A boat might be marked as "accepting crew" on its `BoatResume`, but the calendar/UI will ignore this if the specific race toggle is off.
- **The "Looking" count can be misleading in the UI.** Per commit `6c9b5f3`, a boat that is full but still marked as "accepting" stays in the `boats_looking` count, even though it may drop the count badge in the UI.
- **Crew availability relies on the `crewfinder` opt-in.** A person is only a candidate if `person.preferences.crewfinder.opt_in` is true.
- **Role ambiguity in legacy data.** Per commit `7e6ed14`, the logic must handle `PersonEvent.role` being `NULL` via the inference logic (checking boat ownership) to ensure match counts remain accurate for older records.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Drives the "looking for crew" count badge and the availability summary on the regatta/calendar views.

## External consumers

None known.
