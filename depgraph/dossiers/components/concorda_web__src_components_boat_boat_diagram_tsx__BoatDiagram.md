---
node_id: concorda-web::src/components/boat/boat-diagram.tsx::BoatDiagram
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a6f9c3943a1ba57cb6b6c18b0f22ff897e2bd9c83d23c7e062bf218e036d0fd1
status: current
---

# BoatDiagram

## Purpose

Renders a top-down SVG visualization of a boat hull to represent crew and equipment positions. It translates normalized coordinates (0-100) into a specific SVG viewBox (200x400) to ensure markers are positioned correctly relative to the hull geometry. Use this when you need a non-interactive visual representation or an interactive map of person/object placement on a vessel.

## Invariants

- **Coordinate Scaling** — Input `x` and `y` must be normalized (0-100). The component internally scales `x` to a 20-180 range and `y` to a 30-370 range to keep markers within the hull boundaries.
- **`positions` mapping** — Each position object must contain a `name` (to determine color via `POSITION_COLORS`) and `x`/`y` coordinates.
- **`interactive` prop** — When `true`, the component enables `onPositionClick` and manages internal `hoveredIndex` state for visual feedback.

## Gotchas

- **SVG ViewBox vs. Scaling** — The hull path is hardcoded for a 200x400 viewBox. If the `width` or `height` props are changed significantly without adjusting the `scaleX`/`scaleY` logic, markers may appear outside the hull or misaligned with the visual center.
- **Color Fallback** — If a position `name` is not found in `POSITION_COLORS`, it defaults to `"#6b7280"`.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
