---
node_id: concorda-web::src/components/regatta/regatta-detail-sections.tsx::Dash
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c251edcae0ba3a98c25c394db077a116cb7942b78e41e5379cce8fa38d67ba69
status: current
---

# Dash

## Purpose

The `Dash` component is a visual placeholder used to represent missing or null data in the regatta detail view. It renders a muted em-dash (`—`) to maintain layout consistency when a regatta property (like `first_warning` or `max_races`) is undefined or null. It is a stateless functional component used exclusively for visual fallback.

## Invariants

- **Returns a static JSX element.** It always returns a `<span>` containing a single em-dash character.
- **Uses `text-muted-foreground`.** The visual style is intentionally de-emphasized to distinguish it from actual data.
- **Stateless.** It does not accept props and does not rely on any external context or hooks.

## Gotchas

- **Layout stability.** Per commit `3aada74`, the order of the detail panel was refactored to promote the "Documents & Links" row to the top; `Dash` is used within `Cell` components to ensure that empty fields do not collapse the grid layout or cause alignment shifts in the `grid-cols-2 md:grid-cols-4` structure.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `RegattaDetailSections` to populate the regatta detail panel.

## External consumers

None known.
