---
node_id: concorda-web::src/app/members/scoring/page.tsx::ScoringPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 00d4b80d734fe3d90b855a576cfe74bb6da067778d7a58c4a50059c97d133e07
status: current
---

# ScoringPage

## Purpose

Renders the "Scoring" content page for the MBSA Offshore Season. It acts as a hybrid layout that splits a single markdown source file into two distinct sections: a top section for general context and a bottom section for worked examples. This allows the `ScoringPage` to serve as both a descriptive text component and a functional display for the `ChipsScoringTable`.

## Invariants

- **Content is split by `SPLIT_MARK`** — The string `### Pursuit Race Scoring — Worked Example` is the hard-coded delimiter used to separate the introductory text from the technical examples.
- **`stripLeadingH1` is required** — The content must be processed via `stripLeadingH1` to ensure the page title doesn't repeat the H1 from the markdown source.
- **`top` section is always rendered** — The content before the `SPLIT_MARK` is treated as the primary header/intro and is always passed to the first `Markdown` component.

## Gotchas

- **Manual split dependency** — If the `SPLIT_MARK` constant is changed or the string in the "scoring" content file is edited (e.g., changing a dash to an em-dash), the `bottom` section will fail to render or the `top` section will include the divider.
- **`SPLIT_MARK` is a single-point-of-failure** — Per commit `d647124`, this page is part of the new "yearbook content pages" pattern where content is pulled from a central source; any mismatch between the constant in this file and the actual text in the `scoring` content file breaks the layout.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
