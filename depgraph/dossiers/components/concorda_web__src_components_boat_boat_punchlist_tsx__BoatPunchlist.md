---
node_id: concorda-web::src/components/boat/boat-punchlist.tsx::BoatPunchlist
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 431477e097e721ccf70b46e16c9cb94582a9b65dda6669171f806c322372235a
status: current
---

# BoatPunchlist

## Purpose

The `BoatPunchlist` component manages the lifecycle of maintenance or task items (punchlist) for a specific boat. It provides a UI for viewing, filtering by status (Open, In Progress, Done), adding new items via a form, and deleting existing items. It is a specialized management interface that relies on `boatApi` for all mutations and expects an `onRefresh` callback to sync the parent state after any change.

## Invariants

- **Requires `boatId`** — All API calls (`createPunchlistItem`, `updatePunchlistItem`, `deletePunchlistItem`) are scoped to this ID.
- **Status values are strict** — The `statusFilter` and item updates must use the values defined in `STATUS_OPTIONS` (`open`, `in_progress`, `done`).
- **Mutation triggers `onRefresh`** — Any successful creation, status change, or deletion must call the passed `onRefresh` prop to ensure the parent component's state reflects the new server-side reality.
- **Empty title prevention** — The `handleCreate` function returns early if `title.trim()` is empty, preventing the creation of nameless items.

## Gotchas

- **Mobile layout regression** — Per commit `ab4aef4`, the `add-item` row in the punchlist can cause stacking issues on mobile devices. Ensure any changes to the form or item rows maintain layout stability for smaller screens.
- **`description` is optional** — The `handleCreate` function passes `undefined` to the API if the description is empty, which is the expected behavior for the backend.

## Cross-cutting concerns

- **Auth**: Relies on `boatApi` which requires a valid session/token (implicitly handled by the API client).
- **Side effects**: Triggers `onRefresh` on the parent component, which typically updates the boat's dashboard or profile view.

## External consumers

None known.
