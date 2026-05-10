---
node_id: concorda-web::src/components/boat/boat-specs-card.tsx::Spec
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 38be2af83227783b5f5ac7a7fab2e806f59623dfc088d16b1a7b8e8e48d76c0f
status: current
---

# Spec

## Purpose

A low-level presentational helper used to render a single key-value pair within the `BoatSpecsCard`. It standardizes the visual hierarchy of boat metadata (e.g., Class, Manufacturer, Length) by applying consistent typography for the label and the value. Use this when adding new technical specifications to the boat profile to ensure the UI remains uniform.

## Invariants

- **Input is strictly string-based.** Both `label` and `value` must be strings to satisfy the component's type signature.
- **Visual hierarchy is fixed.** The label is always rendered with `text-muted-foreground` and `text-xs`, while the value uses `font-medium`.

## Gotchas

- **Implicit string conversion.** As seen in the parent component (line 31), numeric values like `boat.length` are passed as template literals (e.g., `` `${boat.length} ft` ``) to satisfy the `value: string` requirement. Passing a raw number will cause a TypeScript error.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
