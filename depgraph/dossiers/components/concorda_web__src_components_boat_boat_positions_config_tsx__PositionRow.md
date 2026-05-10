---
node_id: concorda-web::src/components/boat/boat-positions-config.tsx::PositionRow
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b29e18282b16e071cdb63dea9631ab3ca3232c845fb29cec208b25cdef80e11f
status: current
---

# PositionRow

## Purpose

A UI row component used to manage and display the count of a specific boat position (e.g., "Skipper" or "Crew"). It provides controls to toggle the position's active state and increment/decrement the count via `onSetCount`. It is a sub-component of the boat configuration interface, used to render individual entries within a list of position presets.

## Invariants

- **`count` determines visibility of controls.** The increment/decrement buttons and the count display only appear if `count > 0`.
- **`onToggle` drives the `active` state.** The checkbox state is derived from `count > 0`.
- **`onRemove` is optional.** If the `onRemove` prop is not provided, the "X" (delete) button is not rendered.
- **Uses `tabular-nums` for the count.** The count display uses `tabular-nums` to prevent layout jitter when the number of digits changes.

## Gotchas

- **Mobile layout reflow.** Per commit `189dcf9`, this component (and its parent container) requires careful handling of stacking/reflow to ensure the +/- buttons remain accessible on small screens.
- **Visual feedback for active state.** The row changes its border and background color (`border-primary bg-primary/5`) when `count > 0` to visually distinguish active positions from inactive ones.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Updates the boat configuration state, which is a dependency for the boat profile and owner view displays.

## External consumers

None known.
