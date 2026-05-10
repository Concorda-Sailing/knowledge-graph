---
node_id: concorda-web::src/components/profile/sailing-resume-presentation.tsx::FieldLabel
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1ba508c1277b02618c06a2a1575de3660a3d3a585b650f7ca1190193f89f8113
status: llm_drafted
---

# FieldLabel

## Purpose

A small, purely presentational component used to render labels for the sailing resume. It provides a consistent typographic style (small, uppercase, neutral-colored text) for metadata keys. It is distinct from `SectionHeading`, which is used for larger structural breaks.

## Invariants

- **Accepts `children` as a React node.** It is designed to wrap text or small icons.
- **Uses fixed typography.** The styling is hardcoded to `text-[10px] uppercase tracking-wider text-neutral-500`.
- **Purely presentational.** It does not hold state or interact with any profile or resume data directly.

## Gotchas

- **Avoid using for primary headings.** Per the visual hierarchy in `SailingResumePresentation`, this is a sub-label component; using it for main section titles will break the visual weight established by `SectionHeading`.
- **Text overflow.** Because it uses `uppercase` and `tracking-wider`, long labels may visually "stretch" more than expected in tight layouts.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
