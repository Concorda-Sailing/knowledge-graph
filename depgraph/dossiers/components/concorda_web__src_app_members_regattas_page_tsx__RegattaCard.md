---
node_id: concorda-web::src/app/members/regattas/page.tsx::RegattaCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e16df73080765e50fa4d60e5d25859d4862f6aedb85a8b8a3470c102ef93854e
status: llm_drafted
---

# RegattaCard

## Purpose

The `RegattaCard` is a visual representation of a single regatta within a list view (likely a schedule or calendar). It displays high-level metadata including the date (formatted via the organization's timezone), the organizing authority (OA) with associated links, and location/region details. It serves as a functional entry point for user actions like selecting, toggling, or adding a regatta to a schedule.

## Invariants

- **Timezone-aware rendering**: The `dateInfo` must be derived using `formatDate(regatta.start, tz)` to ensure the date displayed matches the organization's local time, not the user's browser.
- **OA-driven location**: The `region` and `primaryOrg` are derived strictly from the `organizing_authorities` array; the `regatta.location` field is used only as a fallback for the venue line to prevent empty-state UI gaps.
- **Link safety**: If an OA has a website, the link is rendered with `target="_blank"` and `rel="noopener noreferrer"`. The URL is sanitized to ensure it starts with `https://` if a protocol is missing.
- **Event propagation**: `onClick` events on the `Checkbox` and the `<a>` tags must call `e.stopPropagation()` to prevent triggering the card's primary `onSelect` or `onToggle` actions.

## Gotchas

- **Timezone regression**: Per commit `f444b4c`, all backend datetimes must be rendered in the organization's timezone (`tz`) rather than the browser's local time to avoid displaying the wrong day/time to users in different regions.
- **Visual state hierarchy**: The card's styling (ring/background) depends on a specific precedence: `selected` (primary ring) > `added` (primary/30 ring) > `isPast` (opacity-50).
- **Empty state fallback**: If no OA is assigned, the component must fall back to `regatta.location` to ensure the row remains anchored to a physical place.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Changes to the regatta state (via `onToggle` or `onAdd`) affect the visibility of the "Accepting-Crew" badge and the "Upcoming" status in the regatta detail view (per commit `2d6b8a7`).

## External consumers

None known.

## Open questions

- Should the `onSelect` action trigger a full navigation to a detail page, or should it remain a lightweight selection for the drag-and-drop/scheduling flow?
