---
node_id: concorda-api::schemas/regatta.py::RosterCrew
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 439ec41cb69a2032b98fbfaf49cf2144c1ce7cf00ad5e5e51476b6ca6048ce9f
status: current
---

# RosterCrew

## Purpose

Defines the schema for an individual crew member within a regatta roster. It encapsulates identity data (`person_id`, name, picture) alongside sailing-specific metadata (`experience_level`, `years_sailing`) used to match sailors to available positions. This is a sub-model used primarily within the `MatchRoster` structure to represent the human element of a boat's composition.

## Invariants

- **`person_id` is required.** While names and pictures are optional, the link to the `Person` entity is the primary identifier.
- **`positions_preferred` is a list of strings.** This allows for multi-role preference (e.g., ["helmsman", "fore"]) during the matching process.
- **`years_sailing` is an integer.** This is used for filtering/sorting experience levels in the crew-finder logic.

## Gotchas

- **`accept_crew_requests` toggle dependency.** Per commit `6c9b5f3`, the visibility and availability of crew members in the UI is driven by the `accept_crew_requests` boolean on the parent `SailingEvent`. If this toggle is false, the roster logic/display behavior changes.
- **Data density/Optionality.** Many fields (`first_name`, `last_name`, `picture_url`, `experience_level`) are `Optional`. Downstream consumers (like the web frontend) must handle `None` values gracefully to avoid rendering errors when a user has not completed their profile.

## Cross-cutting concerns

- **Auth**: Subject to the same permissions as the parent `SailingEvent` (typically requires organizer or participant-level access to view full details).
- **Side effects**: Changes to `RosterCrew` data (like updating `experience_level`) may affect the ranking/matching logic in the "Crew Finder" feature.

## External consumers

- Web frontend (Regatta/Match Roster views).
- Mobile/Expo (via the API) for displaying crew profiles in event details.
