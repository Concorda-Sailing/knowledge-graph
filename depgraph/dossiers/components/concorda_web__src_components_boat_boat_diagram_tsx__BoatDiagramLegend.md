---
node_id: concorda-web::src/components/boat/boat-diagram.tsx::BoatDiagramLegend
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 59856e81c4b8c2bf92a583024766e0fd821224af48379433c6cfe6c656729fb1
status: current
---

# BoatDiagramLegend

## Purpose

Renders a visual legend for crew positions within a boat diagram. It maps an array of `Position` objects to a series of color-coded dots and text labels, providing a quick reference for the user to identify which parts of the boat are currently occupied or active.

## Invariants

- **Input is an array of `Position` objects.** Each object must contain a `name` (string) and a `filled` (boolean) property.
- **Color is derived from `pos.name`.** The component relies on the `getColor` helper to ensure the legend dot matches the color used in the main SVG diagram.
- **Opacity indicates state.** If `pos.filled` is `false`, the dot's opacity is set to `0.4` to visually represent an inactive or empty position.

## Gotchas

- **Key generation relies on `pos.name` and index.** The `key` is constructed as `` `${pos.name}-${i}` `` to prevent reconciliation issues if position names are duplicated or if the list order changes during a state update.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
