---
node_id: concorda-web::src/components/regatta-icons.tsx::IconSquare
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8cb15ed01611ccb64a2560d1f04f34a3e2724845602b5cb2689cb204b13b194b
status: current
---

# IconSquare

## Purpose

A low-level UI primitive for rendering colored, square-shaped badges or icons. It provides a consistent visual language for status indicators, specifically handling the `stripe` overlay used for "Qs" (partial-qualifier) badges. Use `IconSquare` directly for custom colored badges, but use `QualifierBadge` if you are rendering a standard regatta qualifier code to ensure the correct background color and stripe logic are applied.

## Invariants

- **`bg` must be a Tailwind color class** (e.g., `bg-blue-500`). The component relies on the `bg` prop to set the background color via class name.
- **`children` determines font size.** If the text length is $> 3$ characters, the font size automatically shrinks to `text-[8px]` to prevent overflow.
- **`stripe` is a boolean overlay.** When `true`, it applies a `repeating-linear-gradient` via the `stripeStyle` object to create a diagonal pattern over the background color.
- **`size` dictates dimensions.** The `size` prop (expected to be `sm` or `md`) controls both the height/width and the internal font size.

## Gotchas

- **Text truncation/overflow.** Because the `fontSize` is derived from `text.length`, very long strings passed as `children` will not wrap but will instead trigger the `text-[8px]` class. This can lead to visual clipping if the string is long and the `size` is `sm`.
- **`stripe` visibility.** The stripe uses `rgba(255,255,255,0.45)` at a 135-degree angle. If a background color is extremely light, the stripe may be difficult to see or may clash with the text legibility.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: Used by `QualifierBadge` to render the "Q" (partial-qualifier) visual state, which is a core part of the "shared icon language" introduced in commit `d647124`.

## External consumers

None known.
