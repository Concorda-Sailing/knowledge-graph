---
node_id: concorda-web::src/components/boat/boat-positions-config.tsx::totalCrew
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3ec0b2c8600b91b319bf6c487cf85bf96bb086bc211d167613678a9163e9d73e
status: current
---

# totalCrew

## Purpose

Calculates the aggregate number of crew members across all position configurations for a given boat. It reduces an array of `BoatConfigPosition` objects by summing their `count` values, defaulting to `1` if a count is missing. This is used to determine the total crew capacity required for a specific boat configuration.

## Invariants

- **Input is an array of `BoatConfigPosition` objects.**
- **Missing `count` defaults to `1`.** The function uses the nullish coalescing operator `(p.count ?? 1)` to ensure a numeric return even if the API provides a null or undefined count.
- **Returns a `number`.** The result is a primitive number representing the sum of all positions.

## Gotchas

- **Implicit count of 1.** Because the function defaults to `1` when `count` is missing, a position without an explicit count is treated as a single person rather than zero. This is a critical distinction for calculating boat capacity vs. empty positions.
- **Dependency on `positionsToApi` logic.** While this is a pure calculation, the semantic meaning of the sum depends on the `positionsToApi` transformation used in `seedDefaultConfigs` (line 89) to ensure the data structure is consistent.

## Cross-cutting concerns

- **Auth**: None (pure utility function).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Indirectly affects the accuracy of the "crew count" logic mentioned in commit `f0d48bc`.

## External consumers

None known.
