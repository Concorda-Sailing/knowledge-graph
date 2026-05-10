---
node_id: concorda-web::src/components/profile/sailing-resume-presentation.tsx::EntryList
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cec835f284decb0848cf9ec12c20e14bdccb9706113d24dd21aa913d86d6d664
status: llm_drafted
---

# EntryList

## Purpose

Renders a chronological list of sailing experience entries (e.g., past roles, boats, or positions). It takes an array of objects containing a name and optional metadata (year, boat, role) and displays them as a formatted list. This is a sub-component used within the larger `SailingResumePresentation` to organize historical data.

## Invariants

- **Input items** must follow the shape `{ name: string; year?: number | null; boat?: string | null; role?: string | null }[]`.
- **Sorting is descending by year.** The list is sorted via `.sort((a, b) => (b.year || 0) - (a.year || 0))` to ensure the most recent experience appears first.
- **Metadata formatting.** If a `role` is present, it is passed through `titleCase`; if a `boat` is present, it is prefixed with `"aboard "`.
- **Empty state handling.** If a `year` is missing, it renders a long dash (`—`) to maintain vertical alignment in the list.

## Gotchas

- **Avoid browser-local date parsing.** Per commit `f444b4c`, datetimes must be handled carefully; while this component primarily uses `year` numbers, the parent component extracts the year from a `join_date` string using `.slice(0, 4)` to avoid the timezone-shifting issues associated with constructing a local `Date` object.
- **Layout stability.** The use of `tabular-nums` and `shrink-0` on the year span is intentional to prevent layout shifts when switching between different numeric widths in the list.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: None. This is a pure presentation component.

## External consumers

None known.
