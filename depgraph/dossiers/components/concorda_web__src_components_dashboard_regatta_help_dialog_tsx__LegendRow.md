---
node_id: concorda-web::src/components/dashboard/regatta-help-dialog.tsx::LegendRow
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6d40aa926ad3e3f1ba1f8e5d7241cb538154c5b94bc0d30c64d7c4c837d7c877
status: llm_drafted
---

# LegendRow

## Purpose

A presentational sub-component used to render a single entry in the `RegattaHelpDialog` legend. It provides a standardized layout for an icon, a title, and a description to explain UI elements (like color-coded status badges or specific icons) to the user. It is a stateless primitive used exclusively within the help dialog to ensure visual consistency in the documentation section.

## Invariants

- **Props are required.** The component expects `icon` (ReactNode), `title` (string), and `description` (string).
- **Layout is fixed.** Uses a flex container with `items-start` and a fixed `w-9 h-9` container for the icon to ensure vertical alignment of text against the icon.
- **Icon sizing.** The icon container is designed to center the provided `icon` within a `bg-muted/60` background.

## Gotchas

- **Icon alignment.** The icon container uses `mt-0.5` to offset the icon slightly, ensuring it aligns visually with the first line of the `title` text.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
