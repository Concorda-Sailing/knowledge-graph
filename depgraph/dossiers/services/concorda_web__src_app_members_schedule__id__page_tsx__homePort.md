---
node_id: concorda-web::src/app/members/schedule/[id]/page.tsx::homePort
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 30362b3b9179116f1f16a64ba7cf38baaf114c89ef39e0ad86d42f66417d27b4
status: llm_drafted
---

# homePort

## Purpose

A helper function that generates a human-readable location string for a `Boat` object. It concatenates the `location_club`, `location_city`, and `location_state` from the boat record, filtering out any null or undefined values to ensure a clean, comma-separated string. It is used to display the boat's home base within the schedule detail view.

## Invariants

- **Input is a `Boat` object.** The function expects a valid `Boat` type containing location properties.
- **Output is a comma-separated string.** It joins non-empty elements with `", "`.
- **Filters empty values.** Uses `.filter(Boolean)` to ensure that if a city or state is missing, the string does not contain awkward double commas or leading/trailing punctuation.

## Gotchas

- **Implicitly assumes `location_club` is the primary identifier.** While it provides a human-readable string, it is a derived display value and not a unique identifier for the boat.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
