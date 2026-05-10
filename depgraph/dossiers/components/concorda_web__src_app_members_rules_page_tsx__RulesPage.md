---
node_id: concorda-web::src/app/members/rules/page.tsx::RulesPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 7d894b7fdf0b2f00bb88af7f1d72d7d0fcd60861ae50ce6eafa5eea5d9c1db5d
status: llm_drafted
---

# RulesPage

## Purpose

The `RulesPage` component renders the organization's official sailing instructions and scoring examples. It performs a structural split on the raw markdown content using a hardcoded delimiter to inject the `ChipsScoringTable` component between the general instructions and the pursuit-specific examples. This ensures the scoring table is visually integrated into the text flow rather than appearing as a separate page or a simple footer.

## Invariants

- **Content is split by `SPLIT_MARK`** — the string `"#### Pursuit Race Scoring — Worked Example"` is the required anchor for the layout.
- **`GSI_PDF_URL` is a static external link** — it points to a specific PDF hosted on the `massbaysailing.org` WordPress domain.
- **`top` content is rendered first** — the section before the split mark is passed to the first `<Markdown />` component.
- **`bottom` content is rendered last** — the section from the split mark onwards is passed to the second `<Markdown />` component.

## Gotchas

- **Manual content synchronization required** — per commit `9e333c6`, the `GSI_PDF_URL` and the content structure must be manually updated when the 2026 source documents are released to ensure the PDF link and the text split remain valid.
- **Brittle split dependency** — the layout relies on the exact string `SPLIT_MARK` being present in the `readContent("rules")` output; if the markdown header is changed in the source data, the `ChipsScoringTable` will fail to inject between the text sections.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
