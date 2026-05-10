---
node_id: concorda-web::src/lib/datetime.ts::partsInTz
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 52b8b7ab5296a2966463d9073ed14767e2bdfd34fac10ab8a7b3a5ed9b2a9313
status: llm_drafted
---

# partsInTz

## Purpose

Extracts the individual date/time components (year, month, day, etc.) of a `Date` object as localized strings relative to a specific timezone. It serves as the low-level engine for the `utcIsoToOrgInput` and `orgInputToUtcIso` helpers, ensuring that when a user types a "wall-clock" time into a browser input, the resulting UTC value is calculated based on the organization's timezone rather than the user's local browser timezone.

## Invariants

- **Uses `en-US` locale** — The `Intl.DateTimeFormat` is hardcoded to `en-US` to ensure consistent component keys (year, month, day, etc.) regardless of the user's browser language.
- **Returns a `Record<string, string>`** — Every key is a string representing a part of the date-time (e.g., "year", "month", "day", "hour", "minute", "second").
- **`hourCycle` is fixed to `"h23"`** — This ensures the `hour` component is always a 24-hour format, preventing ambiguity in the `orgInputToUtcIso` calculation.
- **Input is a standard `Date` object** — The function expects a valid JS Date object to perform the internal `formatToParts` call.

## Gotchas

- **DST "Spring Forward" / "Fall Back" ambiguity** — Per the source notes, during the "fall back" hour, the function maps to the first occurrence (the offset before the change). Because race scheduling does not occur at 2:30 AM, this edge case is considered safe for current business logic.
- **Avoid `Date.toISOString()` for form inputs** — Using standard ISO strings directly on `<input type="datetime-local">` will cause the value to shift based on the editor's browser timezone. This function must be used to bridge the gap between the UTC wire format and the local wall-clock display.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: Used by all form-based datetime inputs in the web app to ensure the "wall-clock" time matches the organization's timezone.

## External consumers

None known.
