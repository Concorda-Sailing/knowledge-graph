---
node_id: concorda-web::src/app/join/page.tsx::WaveDivider
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 01249f2f0c47d2753080869cf7905bb026c88e7a8715bee490a60f3a3d52df6b
status: llm_drafted
---

# WaveDivider

## Purpose

A decorative SVG component used to create visual separation between sections of the landing/join page. It renders a multi-layered wave shape that can be inverted using the `flip` prop to create a seamless transition between a hero section and a content section.

## Invariants

- **`flip` prop is boolean.** When `true`, the entire container receives a `rotate-180` class to invert the wave direction.
- **`className` is additive.** The component accepts a `className` string to allow for margin or padding overrides from the parent.
- **SVG uses `preserveAspectRatio="none"`.** This ensures the wave stretches to fill the width of its container, regardless of the aspect ratio.
- **Colors are tied to CSS variables.** The paths use `fill-primary/[0.06]` and similar opacity-scaled classes to ensure the wave matches the theme's primary color.

## Gotchas

- **The `rotate-180` transform affects layout spacing.** Because the rotation is applied to the wrapper `div`, any `padding` or `margin` passed via `className` might behave unexpectedly relative to the visual "peak" of the wave.
- **Hardcoded height.** The SVG height is fixed at `h-[60px] sm:h-[80px]`. If a designer requests a much taller or more dramatic wave, this component must be updated, as it is not purely proportional to the container height.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
