---
node_id: concorda-web::src/app/members/regattas/page.tsx::groupByMonth
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 98ab517d1ebc22d9c0d9644d43839630e658149330bfdfff57d78405fc4cd241
status: current
---

# groupByMonth

## Purpose

Groups an array of `RegattaDetail` objects into a `Map` keyed by a month identifier. This is used to provide a chronological structure for the regatta list, allowing the UI to render headers for specific months and years. It relies on `formatDate` to generate the `monthKey` and `label` to ensure the grouping matches the organization's timezone-aware display logic.

## Invariants

- **Input is `RegattaDetail[]` and `tz: string`**. The function requires a timezone string to ensure the `monthKey` is calculated relative to the organization's local time.
- **Returns a `Map<string, { label: string; monthNum: number; regattas: RegattaDetail[] }>`**. The map key is a string in the format `YYYY-MM` (e.g., `"2026-05"`).
- **Skips regattas without a start date**. If `regatta.start` is falsy, the entry is ignored to prevent grouping errors.
- **`monthKey` is the primary grouping factor**. The `monthNum` and `label` are derived from the `regatta.start` date via `formatDate` to ensure the UI label matches the key.

## Gotchas

- **Timezone dependency**: Per commit `f444b4c`, all grouping and date rendering must use the organization's timezone (`tz`) rather than the browser's local time to prevent regattas from "jumping" months due to offset-induced date shifts.
- **Empty `monthKey` handling**: If `formatDate` returns an empty string (e.g., due to an invalid date or timezone mismatch), the regatta is skipped via `if (!monthKey) continue`.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: Drives the chronological ordering of the regatta list in the main `RegattasPage` view.

## External consumers

None known.
