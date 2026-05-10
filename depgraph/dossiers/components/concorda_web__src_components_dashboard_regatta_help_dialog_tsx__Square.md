---
node_id: concorda-web::src/components/dashboard/regatta-help-dialog.tsx::Square
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5a0abd1dd14b601489cfd3ee76d3fd27473e019bf2408e4a0b5490527b0122f0
status: current
---

# Square

## Purpose

The `Square` component is a specialized visual primitive used to render small, square status indicators or icon containers within the `RegattaHelpDialog`. It is distinct from a standard `Badge` or `Avatar` because it dynamically adjusts its font size based on the length of the text content to ensure legibility within a fixed `h-7 w-7` footprint.

## Invariants

- **Fixed dimensions** — The component is strictly `h-7 w-7` to maintain alignment within the layout.
- **Dynamic font sizing** — If `children` is a string with more than 3 characters, the font size drops to `text-[8px]`; otherwise, it is `text-[10px]`.
- **Coloring** — The `bg` prop must be a valid Tailwind color class (e.g., `bg-primary/10`) to ensure the background is visible.

## Gotchas

- **Text length sensitivity** — Because the font size is tied to `text.length`, passing complex React elements or long strings can cause the text to overflow the `h-7 w-7` container or trigger the smaller `text-[8px]` class.
- **String type check** — The component explicitly checks `typeof children === "string"` to determine font size; passing a non-string child (like a component) results in an empty string for the length calculation, defaulting to `text-[10px]`.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
