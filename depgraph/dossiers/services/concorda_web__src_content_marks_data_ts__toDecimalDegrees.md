---
node_id: concorda-web::src/content/marks-data.ts::toDecimalDegrees
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: af5e5101a415a0f22516341383e4b7bee7b4754c5028d96b51f8359235f8f0f1
status: current
---

# toDecimalDegrees

## Purpose

Converts a string-based coordinate in "Degrees + Decimal Minutes" format (e.g., `"42.17.8"`) into a signed decimal degree number. This is used to transform human-readable/legacy coordinate strings from the `marks-data.ts` constant into a numeric format suitable for mapping and geospatial calculations. It is distinct from `formatCoord`, which performs the inverse operation for display purposes.

## Invariants

- **Input format is "DD.MM.MMMM" or "DD.M"** — The function expects a string where the first dot separates degrees from minutes, and subsequent dots (if any) represent decimal parts of the minutes.
- **Returns a signed number** — The `hemisphere` argument determines the sign; if `hemisphere === "W"`, the resulting decimal degree is negated.
- **Degrees are extracted via `slice`** — The function treats the portion before the first dot as the integer degree component.

## Gotchas

- **Manual parsing logic** — The function does not use a standard library for parsing; it manually calculates `totalMinutes` by splitting the string at the first and second dots. If the input string format deviates from the expected `DD.MM.MMMM` pattern (e.g., using commas or different delimiters), the `Number()` conversions may return `NaN` or incorrect values.
- **Implicit sign handling** — The function relies entirely on the `hemisphere` argument to apply the negative sign for Western longitudes. If a developer attempts to pass a negative number as a string (e.g., `"-70.54.8"`), the behavior of the `degrees` calculation may become unpredictable.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Used for calculating positions of marks/buoys in the racing yearbook content (per commit `d647124`).

## External consumers

None known.
