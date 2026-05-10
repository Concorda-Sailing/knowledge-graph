---
node_id: concorda-web::src/components/dashboard/position-initial.ts::positionInitial
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c8155190f17f51ded0170075d773aae0cc72addab63a06ddc9b1d5084ce27fd1
status: llm_drafted
---

# positionInitial

## Purpose

The `positionInitial` function generates a short visual identifier (initials or abbreviation) for a crew member's position. It is used to provide compact labels within the `PositionSlotGrid` layout. This function is distinct from full name rendering; it prioritizes brevity for UI density.

## Invariants

- **Input is a string** representing a crew position (e.g., "Helm", "Navigator").
- **Returns a string of length 1 or 2.** If the name is found in `ABBREV`, it returns the mapped short string; otherwise, it returns the first two characters of the input in uppercase.
- **Case-sensitivity:** The lookup in `ABBREV` is case-sensitive.

## Gotchas

- **Extraction logic was recently moved.** Per commit `69086bd`, this logic was extracted into a shared helper to avoid duplication in the dashboard components. Ensure any new position abbreviations added to the `ABBREV` object match the exact casing used in the data source to avoid falling back to the `.slice(0, 2)` behavior.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Affects the visual density of the `PositionSlotGrid` in the dashboard.

## External consumers

- `PositionSlotGrid` in `concorda-web/src/components/dashboard/position-slot-grid.tsx`.
