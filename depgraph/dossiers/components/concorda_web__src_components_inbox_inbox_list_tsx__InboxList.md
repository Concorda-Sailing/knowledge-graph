---
node_id: concorda-web::src/components/inbox/inbox-list.tsx::InboxList
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f659b6147898000ccf20f4b49e3d62057654df2085682eb3aa2c888f0c9d4523
status: llm_drafted
---

# InboxList

## Purpose

The central aggregator for the user's pending action items. It orchestrates the display of three distinct types of requests: incoming approvals, outgoing approvals, and crew requests. It serves as the high-level container that manages the loading states and the unified `refreshAll` trigger used by its children to update the list after an action is taken.

## Invariants

- **Aggregates three distinct hooks**: Uses `usePendingApprovals` for incoming/outgoing flows and `useInboxCrewRequests` for crew-specific data.
- **`canManageBoats` permission check**: Determines if the user has `grants_boat_management` via `useAuth` to enable/disable specific row actions.
- **Unified Refresh**: The `refreshAll` callback must trigger both `refresh` from `usePendingApprovals` and `refreshCrewRequests` from `useInboxCrewRequests` to ensure the entire inbox view is consistent.
- **Empty State Logic**: The "all caught up" view is only rendered if all three data arrays (`incoming`, `outgoing`, and `crewRequests`) are empty.

## Gotchas

- **Visibility during refresh**: Per commit `aaadecd`, the component must ensure existing rows remain visible during a refresh to prevent UI flickering or "jumping" when a user triggers an action.
- **Loading state priority**: If any of the underlying hooks are loading, the component shows a "Loading..." text rather than the empty state, even if the arrays are empty.

## Cross-cutting concerns

- **Auth**: Depends on `useAuth` to determine `grants_boat_management` for boat management capabilities.
- **Side effects**: Triggers a full refresh of the inbox view when any child row (Incoming, Outgoing, or Crew) calls `onChanged`.

## External consumers

None known.

## Open questions

- The `InboxList` is currently a passive aggregator; should it eventually handle the "composer" logic for creating new requests, or should that remain in a separate sibling component?
