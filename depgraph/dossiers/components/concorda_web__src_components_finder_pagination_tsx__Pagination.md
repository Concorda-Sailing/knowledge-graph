---
node_id: concorda-web::src/components/finder/pagination.tsx::Pagination
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6adc8ee7ed07fec030a0c7a5f6313f50fe095a8ee36d30d362db3af00bd056a0
status: llm_drafted
---

# Pagination

## Purpose

A stateless UI component for navigating paginated lists. It provides "Previous" and "Next" buttons with automatic disabling of edge-case buttons (first/last page) and displays the current page index. Use this instead of custom button-based navigation when displaying results from the `BoatFinderPanel` or `CrewFinderPanel` to ensure consistent spacing and icon usage.

## Invariants

- **Returns `null` if `totalPages <= 1`** — the component is invisible if there is no navigation required.
- **`page` is 1-indexed** — the `onPageChange` logic assumes the current page is at least 1.
- **`onPageChange` is the sole driver of state** — this component does not manage its own state; it only notifies the parent of an intent to change.
- **Buttons are disabled at boundaries** — the "Left" button is disabled when `page <= 1` and the "Right" button is disabled when `page >= totalPages`.

## Gotchas

- **Layout shifts** — because the component returns `null` when `totalPages <= 1`, the parent container may experience a layout jump if the list size changes from 1 page to multiple pages.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: None.

## External consumers

None known.
