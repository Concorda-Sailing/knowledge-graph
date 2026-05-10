---
node_id: concorda-web::src/app/members/scoring/scoring-table.tsx::ChipsScoringTable
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5148859f22104696738afeb6f6661bef16ddfd60d41c724dd6f194651a6d87ca
status: llm_drafted
---

# ChipsScoringTable

## Purpose

Renders the MBSA Offshore Season Scoring System (CHIPS) matrix as a static HTML table. It is used to display the scoring logic for the offshore season, specifically how points are awarded based on finishing position and the number of racers. It is a purely presentational component that relies on static data imported from `@/content/scoring-data`.

## Invariants

- **Static Data Dependency** — The table structure, including headers and the N+1/N+2 rows, is driven by `CHIPS_RACER_COLUMNS`, `CHIPS_TABLE`, `CHIPS_NPLUS_1`, and `CHIPS_NPLUS_2`.
- **Sticky First Column** — The first column (`Position`) uses `sticky left-0` to ensure the position label remains visible during horizontal scrolling on small viewports.
- **Tabular Alignment** — Uses `font-mono` and `tabular-nums` for all numeric cell contents to ensure vertical alignment of decimal/integer values.
- **Null Handling** — If a point value is null or undefined, it renders a dash (`—`) with `text-muted-foreground` rather than an empty cell.

## Gotchas

- **Manual Data Sync** — Because this component relies on hardcoded constants from `@/content/scoring-data`, any change to the official MBSA scoring rules requires a manual update to the data file rather than a database change.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
