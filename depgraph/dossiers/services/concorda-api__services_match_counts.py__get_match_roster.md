---
node_id: concorda-api::services/match_counts.py::get_match_roster
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ea1d84413713dbb03ed90b7998473ffea4c1c17686376cc3935ce25f2033744b
status: current
---

# get_match_roster

## Purpose

Returns a dictionary containing lists of `boats` and `crew` for a specific regatta, intended for use on the regatta detail page. It acts as a filtered view of the regatta's participants, using boolean flags (`include_boats`, `include_crew`) to control the visibility of specific data types. This allows the frontend to toggle between a high-level overview and a detailed roster without making multiple API calls.

## Invariants

- **Returns a dictionary** with keys `"boats"` and `"crew"`, where each value is a list.
- **`include_boats` and `include_crew` are keyword-only arguments** that act as permission gates; if a flag is `False`, the corresponding list must be empty.
- **The function is idempotent** for a given `regatta_id` and set of database-state-driven roles.
- **Input `regatta_id` is a string** representing the unique identifier for the regatta.

## Gotchas

- **Captain/Crew role inference logic is complex.** Per commit `7e6ed14`, the system now explicitly records roles on bookmarks, but the logic still handles "legacy" users (where `role` is `NULL`).
- **The "Captain" exclusion rule is sensitive.** A person is considered a captain if they have an explicit `role == 'captain'` OR if they are an `owner` of a boat in the current `boat_ids` set (per logic in lines 231-241).
- **Matched exclusion logic:** A person is excluded from the "crew" list if they have an `accepted` status on any `sailing_event` associated with this regatta (lines 243-249).
- **The `boat_ids` set is a prerequisite for certain role inferences.** If `boat_ids` is empty, the `inferred_captain_ids` logic is bypassed, which can change the resulting `skipper_ids` (lines 234-240).

## Cross-cutting concerns

- **Auth**: Relies on the router-level permission gates (implied by the `include_` flags) to ensure users only see the data they are authorized to see.
- **Side effects**: Directly populates the data for the regatta detail page.

## External consumers

- `GET /api/regattas/{regatta_id}/match-roster` (via `routers/regattas.py`)
