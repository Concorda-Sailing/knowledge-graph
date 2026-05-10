---
node_id: concorda-web::src/components/dashboard/event-plan-panel.tsx::positionInitial
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 34065845b8c76c5504c21465daa6528176e08f7eecc3f5bed461ac02550a7435
status: llm_drafted
---

# positionInitial

## Purpose

The `positionInitial` helper generates a short, two-letter (or single-letter) abbreviation for a crew position name. It is used to create compact visual identifiers in the UI for crew members assigned to specific roles. It is distinct from the full role name and provides a fallback mechanism for roles not explicitly defined in the `ABBREV` mapping.

## Invariants

- **Input is a string.** The function expects a role name (e.g., "Helm", "Bow").
- **Returns a string.** It always returns a string of at least 1 character.
- **Fallback logic.** If the name is not found in the `ABBREV` record, it returns the first two characters of the name in uppercase.

## Gotchas

- **Manual mapping requirement.** The `ABBREV` record is a hardcoded dictionary. If a new role is added to the system (e.g., via a new `PositionSlot`), it will default to a two-letter abbreviation (like "XY") unless the developer manually adds it to this function.
- **Case sensitivity.** The fallback `name.slice(0, 2).toUpperCase()` assumes the input is a standard string; if the input is empty or unexpectedly short, it will still return a valid (though potentially empty or single-char) string without throwing.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Affects the visual density of the `EventPlanPanel` UI when rendering crew lists.

## External consumers

None known.
