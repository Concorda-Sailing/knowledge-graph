---
node_id: concorda-web::src/components/dashboard/regatta-help-dialog.tsx::SectionHeading
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bd116f3a4d7395b75d4b27b3c539fea1f1454f2dd08d9f0f7251173d99bb8c0e
status: llm_drafted
---

# SectionHeading

## Purpose

A purely presentational sub-component used to label sections within the `RegattaHelpDialog`. It provides a consistent typographic style for section headers (uppercase, small text, specific spacing) to ensure the "Example" and other instructional headers are visually distinct from the content below them.

## Invariants

- **Accepts `children` as a `ReactNode`** to allow for text or other inline elements.
- **Uses `text-xs` and `uppercase`** to maintain the visual hierarchy of the help documentation.
- **Implements `first:mt-0`** via Tailwind to ensure the first section heading in a stack does not introduce unnecessary top padding.

## Gotchas

- **Visual spacing is hardcoded.** The `mt-5 mb-2` pattern is used to create breathing room between the section title and the annotated `Card` content.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
