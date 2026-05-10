---
node_id: concorda-web::src/app/members/marks/page.tsx::MarksPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: aea5329ce8e169d2766d49c32ddb16832e52a5690e6ea9ded12cd7fb5801a0f1
status: current
---

# MarksPage

## Purpose

The entry point for the "Standard Rounding Marks" yearbook page. It serves as a layout wrapper that pulls in static content via `readContent("marks")` and passes it to `MarksContent`. This page is intended as a reference-only display for organization-specific rounding rules (e.g., MBSA Lists A, B, C) and is not a functional navigation tool.

## Invariants

- **Content source is static-driven** — The page relies on `readContent("marks")` to fetch the raw text; the structure of the page is a wrapper around this content.
- **Uses `stripLeadingH1`** — The `intro` prop passed to `MarksContent` must have the leading H1 removed to prevent redundant title rendering in the UI.
- **Layout is encapsulated in a `Card`** — The page uses a `Card` with `overflow-hidden` to ensure the content-heavy `MarksContent` does not break the layout container.

## Gotchas

- **Content is "reference only"** — Per the `subtitle` in the source, this page is a static reference and should not be used as a navigation or interactive element.
- **Dependency on `readContent`** — If the "marks" key is missing from the content provider, `stripLeadingH1` may receive unexpected input, though `readContent` is the primary failure point.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
