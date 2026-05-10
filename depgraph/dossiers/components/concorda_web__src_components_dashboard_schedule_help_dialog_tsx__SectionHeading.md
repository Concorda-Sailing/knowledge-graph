---
node_id: concorda-web::src/components/dashboard/schedule-help-dialog.tsx::SectionHeading
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bd116f3a4d7395b75d4b27b3c539fea1f1454f2dd08d9f0f7251173d99bb8c0e
status: current
---

# SectionHeading

## Purpose

The `SectionHeading` component provides a standardized, semantic heading for the internal documentation sections within the `ScheduleHelpDialog`. It is a purely presentational sub-component used to structure the "Example" and other instructional segments of the help dialog, ensuring consistent typography and spacing for legend-style text.

## Invariants

- **Accepts `children` as a `ReactNode`** — allows for text or small inline elements.
- **Uses fixed styling** — applies `text-xs font-semibold uppercase tracking-wide text-muted-foreground` to maintain the visual hierarchy of a legend.
- **Implements specific spacing** — includes `mt-5 mb-2` and `first:mt-0` to ensure the first heading in a stack doesn't create excessive top padding.

## Gotchas

- **Visual consistency with sibling components** — This component is a structural twin to the `SectionHeading` used in `regatta-help-dialog.tsx`. Any change to the font size or color should be verified against that component to ensure the "Help Dialog" design language remains unified across the dashboard.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
