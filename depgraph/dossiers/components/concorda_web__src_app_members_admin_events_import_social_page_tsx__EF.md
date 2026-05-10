---
node_id: concorda-web::src/app/members/admin/events/import-social/page.tsx::EF
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3536627b768685f9fb217818be4205e3041ba4c59a0fd1f4927f0f5da34abce2
status: llm_drafted
---

# EF

## Purpose

A local helper component used to render a single labeled input field within the social media import form. It abstracts the `Label` and `Input` pairing to ensure consistent spacing and styling for metadata fields (like handles or platform names) during the spreadsheet import process.

## Invariants

- **Input type is configurable.** The `type` prop defaults to `"text"` but allows for specific types (e.g., `"url"`) to be passed through to the underlying `Input` component.
- **Controlled component pattern.** The `onChange` callback must be provided to lift the state up to the parent form, as the component does not manage its own internal state.
- **Visual consistency.** Uses a fixed height (`h-8`) and small text size (`text-sm`) to keep the import form compact.

## Gotchas

- **Mobile layout reflow.** Per commit `019f6e3`, these types of form elements in admin grids require careful handling of single-column reflows to ensure the `Label` and `Input` stack correctly on mobile devices.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Part of the spreadsheet multi-import flow introduced in `e56387c`.

## External consumers

None known.
