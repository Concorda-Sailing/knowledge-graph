---
node_id: concorda-web::src/components/profile/race-area-selector.tsx::RaceAreaSelector
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 37da3290c5ad3afef72c0a8e2a3c92c8643f04126f9dae2ec6dbb567ae8476be
status: llm_drafted
---

# RaceAreaSelector

## Purpose

A specialized checkbox component for selecting geographic availability within the Boston area. It provides a high-level "Mass Bay" toggle that acts as a master switch for the three sub-areas (north, central, south), alongside individual toggles for each sub-area. Use this when a user profile needs to define specific regional availability for racing.

## Invariants

- **`value` is an array of strings.** The component expects `string[]` and returns the updated array via `onChange`.
- **`BOSTON_SUB_AREAS` is the source of truth.** The sub-area labels and logic are hardcoded to `["north", "central", "south"]`.
- **Indeterminate state logic.** The "Mass Bay" checkbox uses a three-state logic: `true` (all selected), `"indeterminate"` (some selected), or `false` (none selected).

## Gotchas

- **Labeling mismatch.** Per commit `6d9d038`, the top-level label was renamed from "Boston" to "Mass Bay" to better reflect the regional scope. Ensure any text updates or tests reflect this change to avoid visual regressions.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Updates the user's availability profile, which is consumed by the crew finder and event registration systems.

## External consumers

None known.
