---
node_id: concorda-web::src/components/boat/boat-specs-card.tsx::BoatSpecsCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4c01df3e2b35e783615111ef132eccc7d1201ce1a5ffb732ce6b3d781588cb87
status: llm_drafted
---

# BoatSpecsCard

## Purpose

Displays a structured summary of a boat's physical characteristics (sail number, name, class, manufacturer, and length). It is a purely presentational component used to render static metadata within boat-related views. Use this when you need to display the `BoatSpecsLike` object properties in a consistent, two-column grid format.

## Invariants

- **Input is `BoatSpecsLike`** — the component expects an object containing `sail_number`, `name`, `boat_class`, `manufacturer`, and `length`.
- **Length is a number** — the `length` property is treated as a number and appended with `" ft"` for display.
- **Fallback values are hardcoded** — missing strings (name, sail number) default to `"—"` to prevent empty UI gaps.
- **Layout is a 2-column grid** — uses `grid-cols-2` with specific spacing (`gap-x-6 gap-y-3`) for the spec list.

## Gotchas

- **`length` unit assumption** — the component hardcodes the `" ft"` suffix. If the API or data source changes to metric (meters), this component will display incorrect units.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
