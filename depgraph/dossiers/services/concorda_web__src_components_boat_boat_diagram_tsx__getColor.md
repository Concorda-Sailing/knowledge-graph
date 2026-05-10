---
node_id: concorda-web::src/components/boat/boat-diagram.tsx::getColor
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a925db0e90f5f5bb18c606938830782f78ad36a61c5b48f5561e43042d8f7ef
status: current
---

# getColor

## Purpose

The `getColor` helper maps a specific boat position name to a hex color code for visualization within the `BoatDiagram` SVG. It acts as the central source of truth for the visual identity of crew and equipment positions, ensuring that a "Mast" or "Bow" always renders with the same color across different views.

## Invariants

- **Input is a string** representing the position name (e.g., "Bow", "Mast").
- **Returns a hex color string.** If the input name is not found in `POSITION_COLORS`, it defaults to `"#6b7280"` (slate).
- **Colors are hardcoded constants.** The function relies on the `POSITION_COLORS` object defined in the same file.

## Gotchas

- **Implicit fallback behavior.** If a new position type is added to the backend or configuration but not added to `POSITION_COLORS`, it will silently render as slate (`#6b7280`) rather than throwing an error or using a high-visibility color.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: None. This is a pure visual mapping used by the `BoatDiagram` component.

## External consumers

None known.
