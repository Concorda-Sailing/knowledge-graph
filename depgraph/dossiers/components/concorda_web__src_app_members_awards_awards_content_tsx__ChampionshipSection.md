---
node_id: concorda-web::src/app/members/awards/awards-content.tsx::ChampionshipSection
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e1ebcfffca258d71e67241e1ad549ceb37091bc036c430c38ed2f1b30495c87c
status: current
---

# ChampionshipSection

## Purpose

The `ChampionshipSection` component renders the specific details of a championship award, including its title, description, and the qualifying regattas associated with it. It uses the `buildEntries` helper to map raw regatta data and series information into a list of clickable links. This component is distinct from the parent `AwardsContent` in that it focuses strictly on the display logic for a single championship's qualifying criteria, rather than managing the state of the entire awards list.

## Invariants

- **Input types are strictly defined**: `champ` must be a `ChampionshipDef`, `regattas` must be an array of `RegattaDetail`, and `seriesById` must be a `Map<string, SeriesDetail>`.
- **Chronological ordering**: The `buildEntries` helper (used via `useMemo`) sorts entries by the `start` property using `localeCompare` to ensure a predictable temporal sequence in the UI.
- **Link behavior**: All regatta links are configured with `target="_blank"` and `rel="noopener noreferrer"` to ensure external navigation does not disrupt the user's session.

## Gotchas

- **Dependency on `buildEntries` sorting**: Because `entries.sort` is called on the result of `buildEntries`, any change to how `buildEntries` handles or returns the array can break the chronological display logic.
- **`seriesById` Map requirement**: The component expects a `Map` for `seriesById` rather than a plain object; passing a standard object will cause a runtime error during the `buildEntries` execution.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: None.
- **Rate limit**: None.
- **Side effects**: The layout of the "Yearbook" content pages depends on the correct rendering of this section.

## External consumers

None known.
