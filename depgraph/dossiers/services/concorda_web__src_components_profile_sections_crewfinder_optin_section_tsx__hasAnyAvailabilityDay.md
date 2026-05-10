---
node_id: concorda-web::src/components/profile/sections/crewfinder-optin-section.tsx::hasAnyAvailabilityDay
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2aaa78b6fc7480aeba7d005a1b08a152dd5afbf14c5eb73cd7d2401c14646181
status: current
---

# hasAnyAvailabilityDay

## Purpose

A helper function used to determine if a user has any availability days selected. It checks the boolean presence of any day (Monday through Sunday) within the `SailingResume["availability"]` object. This is used by `CrewfinderOptinSection` to determine if the "Racing Preferences" requirement is met for publishing a profile to the Crew Finder.

## Invariants

- **Input is a `SailingResume["availability"]` object or `undefined`.**
- **Returns a boolean.** It returns `true` if at least one day is truthy, and `false` if the object is undefined or all days are falsy.
- **Strictly checks day keys.** It relies on the specific keys `monday` through `sunday` being present on the input object.

## Gotchas

- **Implicitly treats missing days as `false`.** If the `availability` object is partially populated (e.g., only `monday: true`), the function returns `true`. If the object is `undefined`, it returns `false` without throwing.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Determines the visual state (CheckCircle2 vs AlertCircle) of the "Racing Preferences" indicator in the `CrewfinderOptinSection`.

## External consumers

None known.
