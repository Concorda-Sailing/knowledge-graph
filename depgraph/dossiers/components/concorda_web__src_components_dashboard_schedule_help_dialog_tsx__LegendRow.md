---
node_id: concorda-web::src/components/dashboard/schedule-help-dialog.tsx::LegendRow
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 834254f084c2c9d85e715b708aa5c529086e9d5de3869ebb3e8ed9c520fc050d
status: llm_drafted
---

# LegendRow

## Purpose

A private sub-component used to render a single entry in the `ScheduleHelpDialog` legend. It provides a standardized layout for an icon, a title, and a description to explain the meaning of various visual indicators (like badges or status colors) used on schedule cards.

## Invariants

- **Layout structure** — Uses a `flex` container with `items-start` to ensure icons remain aligned even if the description spans multiple lines.
- **Icon sizing** — The icon container is fixed at `w-8 h-8` with `shrink-0` to prevent the icon from collapsing when the description text is long.
- **Text hierarchy** — The `title` uses `text-sm font-medium` while the `description` uses `text-xs text-muted-foreground` to maintain visual distinction.

## Gotchas

- **Visual alignment** — The icon container uses `mt-0.5` to vertically center the icon relative to the first line of text; changing this can cause the icon to look "dropped" or "floating" relative to the title.
- **Component isolation** — This is a non-exported internal component of `ScheduleHelpDialog`. Do not attempt to move it to a shared component library without verifying it doesn't rely on the specific `lucide-react` icon types passed in via props.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
