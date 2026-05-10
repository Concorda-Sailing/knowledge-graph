---
node_id: concorda-web::src/app/members/awards/awards-content.tsx::buildEntries
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2abf178d829dc620d418a696c258fbe125e2ef3456dd64247b7cb1be17d69db0
status: current
---

# buildEntries

## Purpose

Transforms raw regatta and series data into a structured list of `QualifyingEntry` objects for display in the Championship section. It filters regattas based on a provided list of `qualifierCodes`, groups them by their parent `series_uuid`, and determines whether to present a single regatta or a summarized series view. Use this function when you need to convert raw event lists into the specific UI format required for the awards/yearbook display.

## Invariants

- **Input grouping**: Regattas with a `series_uuid` are grouped into a single entry, while regattas without a series are treated as standalone entries.
- **Sorting logic**: Series entries are sorted by the `start` date of their earliest race; the final list is sorted globally by the `start` string.
- **Return shape**: Every entry must contain a `key` (prefixed with `series-` or `regatta-`), a `name`, a `start` timestamp, a `codes` array, and an `href`.
- **Href destination**: For series, the `href` points to the first race in that series to ensure a valid entry point.

## Gotchas

- **Sorting relies on string comparison**: The function uses `localeCompare` on the `start` string (e.g., `a.start.localeCompare(b.start)`). This assumes the `start` field is a lexicographically sortable ISO-8601 string; if the format changes to a non-sortable format, the chronological order of the awards list will break.
- **Series name fallback**: If a `series_uuid` is present but the corresponding `seriesById` map does not contain the ID, the function falls back to using the name of the first race in that group (`races[0].name`).

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Directly populates the list rendered by `ChampionshipSection`.

## External consumers

None known.
