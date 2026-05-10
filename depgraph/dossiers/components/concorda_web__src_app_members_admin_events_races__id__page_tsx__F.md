---
node_id: concorda-web::src/app/members/admin/events/races/[id]/page.tsx::F
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: efbc64b6fd4977a45b1e6eff203c527daf8cdd09506ff78311b6fbe5d67ac647
status: current
---

# F

## Purpose

A local UI helper component used to wrap form fields or display sections with a label and an optional hint. It provides consistent vertical spacing (`space-y-1.5`) and typography for administrative race configuration forms. It is a purely presentational component used to group a `Label` with its corresponding input or content.

## Invariants

- **Layout is vertical**: The component uses `space-y-1.5` to ensure the label, children, and hint are stacked with consistent spacing.
- **Hint is optional**: If `hint` is not provided, the `<p>` tag is not rendered, preventing empty whitespace or broken layouts.
- **Text styling is fixed**: The label is hardcoded to `text-sm` to maintain the administrative form density.

## Gotchas

- **Leading bullet/spacing issues**: Per commit `8cbe76e`, adjustments were made to how elements are displayed when certain fields (like location) are the only ones set; ensure that adding a hint doesn't inadvertently introduce unwanted vertical gaps or bullet-like indentation in the admin/races view.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
