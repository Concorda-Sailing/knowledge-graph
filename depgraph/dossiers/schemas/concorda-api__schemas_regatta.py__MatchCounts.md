---
node_id: concorda-api::schemas/regatta.py::MatchCounts
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f7a3dd35b966fab57642f7c75406b003b02812a0ef4e8e5379032c6eca8aef61
status: current
---

# MatchCounts

## Purpose

The `MatchCounts` schema provides a snapshot of participant density for a specific regatta. It tracks the total number of boats, those currently "looking" (searching for crew), and those "accepting" (available for hire). This is used to drive high-level UI indicators for the "Boat Finder" and crew-matching features.

## Invariants

- **Integer types.** All fields (`boats_total`, `boats_looking`, `crew_available`) must be `int`.
- **Default values.** Fields default to `0` if not explicitly provided, preventing null pointer issues in the frontend.
- **Additive logic.** While not enforced by the schema itself, the sum of these counts is used to determine the availability density of a regatta.

## Gotchas

- **Per-race toggle logic.** Per commit `6c9b5f3`, the "Accepting-Crew" status is driven by a per-race toggle. If a user is looking for crew, the `boats_looking` count is affected by whether the specific race/regatta is toggled to show all on-calendar boats.
- **Denominator dependency.** Per commit `1732f36`, the `accepting_crew` logic is tied to a new config slot denominator; ensure any logic calculating these counts accounts for the relationship between "looking" and "accepting" to avoid mismatched UI counts.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Drives the "Boat Finder" density indicators and the "Accepting-Crew" visibility toggle on the regatta list view.

## External consumers

None known.
