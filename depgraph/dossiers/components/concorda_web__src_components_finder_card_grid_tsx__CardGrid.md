---
node_id: concorda-web::src/components/finder/card-grid.tsx::CardGrid
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 42fd094a3adae93a138314591dbaaeddae4590aee844f8a7c689441f54d52b8a
status: llm_drafted
---

# CardGrid

## Purpose

A layout wrapper for displaying a collection of cards in a responsive grid. It uses CSS `auto-fill` to ensure the grid populates with as many columns as the container width allows, rather than forcing a fixed number of columns. Use this when building "Finder" views (e.g., boat lists, crew lists) to ensure cards don't become unreadably wide on large screens.

## Invariants

- **`minWidth` defaults to `"300px"`** — this ensures cards maintain a readable footprint on mobile and desktop.
- **Uses `min(${minWidth}, 100%)`** — this prevents the grid item from overflowing the viewport on small screens by forcing the width to 100% if the `minWidth` is larger than the available space.
- **Layout is purely structural** — it does not manage the state or content of the children, only their spatial arrangement.

## Gotchas

- **Recent layout refresh** — per commit `7a47845`, this component is part of the "finder components" update for the admin layout refresh. Ensure any new finder-style layouts use this to maintain visual consistency with the new admin UI.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: None.

## External consumers

None known.
