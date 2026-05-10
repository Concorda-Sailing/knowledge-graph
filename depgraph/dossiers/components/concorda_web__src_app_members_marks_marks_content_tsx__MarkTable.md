---
node_id: concorda-web::src/app/members/marks/marks-content.tsx::MarkTable
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 56792b817df3c975457b7e5564b58e61e3c5ca71162f24d1257b1e911a0c8351
status: current
---

# MarkTable

## Purpose

Renders a tabular representation of maritime marks (navigation aids) for a specific list. It accepts a `listId` to select the dataset from `MARK_LISTS` and a `format` string to determine how coordinates are displayed. Use this component when you need to display structured navigation data (designators, symbols, and coordinates) that requires a specific coordinate format (e.g., `dd`, `dmm`, or `dms`).

## Invariants

- **`listId` must be a valid `MarkList` key** from `MARK_LISTS` to avoid undefined access.
- **`format` determines coordinate rendering** via the `formatCoord` helper; changing this affects the visual precision of latitude and longitude columns.
- **`designatorLabel` is context-dependent**: it displays "Letter" if `listId` is "A", otherwise "No.".
- **Empty values fallback to "—"** for `symbol`, `light`, `lat`, `lng`, and `govNum` to ensure the table structure remains intact even with missing data.

## Gotchas

- **Coordinate formatting is sensitive to the `format` prop.** Per commit `f444b4c`, ensure that any coordinate-related rendering in this module respects the organization's timezone/format standards to avoid the "browser-local" drift seen in other datetime components.
- **`m.symbol` and `m.light` use nullish coalescing to "—"**. If a developer attempts to use a conditional render that expects a falsy value to hide a row, it will fail because the component explicitly renders the string "—".

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: The `MarksContent` parent component handles the `fetchLogoDataUrl` logic, which is used to embed the organization's logo into a generated PDF via `jsPDF`.

## External consumers

None known.
