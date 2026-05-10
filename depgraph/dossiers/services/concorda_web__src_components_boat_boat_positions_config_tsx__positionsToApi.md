---
node_id: concorda-web::src/components/boat/boat-positions-config.tsx::positionsToApi
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1827670e23aefd14e3a55ab6df4db1ea1b6227545363274dd492f6d0af1bf75f
status: llm_drafted
---

# positionsToApi

## Purpose

Converts a Map of position names and counts into the `BoatConfigPosition[]` array format required by the `profileApi`. It maps human-readable position names to their corresponding spatial coordinates (`x`, `y`) from the `STANDARD_POSITIONS` constant. This ensures that when a user configures a boat's crew layout, the visual representation on the UI matches the logical data sent to the backend.

## Invariants

- **Input is a `Map<string, number>`** representing position names and their respective counts.
- **Output is an array of `BoatConfigPosition` objects.** Each object must contain `name`, `location_x`, `location_y`, and `count`.
- **Fallback coordinates are `50, 50`.** If a position name is not found in `STANDARD_POSITIONS`, the function defaults to the center of the canvas.
- **Filters zero-counts.** The function only returns positions where the count is greater than 0.

## Gotchas

- **Coordinate dependency:** The accuracy of the visual "dot" on the boat layout depends on the `STANDARD_POSITIONS` lookup. If a new position is added to the UI but not to the `STANDARD_POSITIONS` constant, it will default to the center (`50, 50`), potentially causing overlapping UI elements.
- **Preset mismatch:** The `PRESETS` array relies on specific string names (e.g., "Helm", "Main Trim"). If these strings are modified in the `STANDARD_POSITIONS` definition without updating `PRESETS`, the `seedDefaultConfigs` function will produce positions that default to the center coordinates.

## Cross-cutting concerns

- **Auth**: None (purely a data transformation utility).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Used by `seedDefaultConfigs` to generate initial data for the `profileApi.createBoatConfig` call.

## External consumers

None known.
