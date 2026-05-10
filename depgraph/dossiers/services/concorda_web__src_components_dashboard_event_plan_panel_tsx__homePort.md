---
node_id: concorda-web::src/components/dashboard/event-plan-panel.tsx::homePort
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: eda63882071333a8bfe0bc5f7e657b280396ffb51f918f4b23a371e19dcf4665
status: current
---

# homePort

## Purpose

A helper function that generates a human-readable string representing a boat's home port. It concatenates the `location_club`, `location_city`, and `location_state` from a `Boat` object, filtering out any null or undefined values to ensure a clean, comma-separated string. This is used primarily to set default departure and arrival locations in the `EventPlanPanel` when a boat is selected.

## Invariants

- **Input is a `Boat` object.** The function expects a valid boat object with location properties.
- **Output is a comma-separated string.** It joins `location_club`, `location_city`, and `location_state` with `", "`.
- **Falsy values are filtered.** If a location component is missing, it is skipped rather than leaving trailing commas or "undefined" strings.

## Gotchas

- **Relies on specific `Boat` property names.** If the `Boat` interface changes its location-related field names, this function will return an empty string or break, as it relies on `boat.location_club`, `boat.location_city`, and `boat.location_state`.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Used to populate the `departure_location` and `arrival_location` defaults in the `EventPlanPanel`.

## External consumers

None known.
