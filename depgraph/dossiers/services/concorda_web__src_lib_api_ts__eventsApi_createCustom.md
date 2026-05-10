---
node_id: concorda-web::src/lib/api.ts::eventsApi.createCustom
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 450c894b1b7c3a8cb94cd0ab9ce9bd7c395a98f8dbd4d1aa590e8f1872d334b0
status: llm_drafted
---

# eventsApi.createCustom

## Purpose

Creates a new custom event by combining a generic event with a specific sailing event configuration. This method is used when a user wants to instantiate a new event that isn't part of an existing series or regatta, effectively bridging the gap between a standard `Event` and a `SailingEvent`. Use this instead of `upsertSailingEvent` when the intention is to create a fresh, standalone entry rather than modifying an existing one.

## Invariants

- **HTTP Method is `POST`** — Must be a POST request to `/api/events/custom`.
- **Returns a composite object** — The response shape is `{ event: Event; sailing_event: SailingEvent }`.
- **Requires `CustomEventCreate` payload** — The input must satisfy the structure required to instantiate both the base event and the sailing-specific details.
- **Uses `fetchApiAuthenticated`** — Requires a valid bearer token to authorize the creation.

## Gotchas

- **Dependency on `SailingEvent` structure** — Recent changes in the crew/schedule logic (see commit `bf44b09`) suggest that the relationship between base events and sailing events is sensitive to how types are unioned; ensure the `data` payload aligns with the expected `SailingEvent` properties.
- **Implicit defaults** — While not explicitly in this function, related methods like `addRegattas` (sibling) rely on client-side defaults for `departure_time` (e.g., `dock_time + 45m`). When creating custom events, ensure any time-based fields are explicitly provided if the backend doesn't handle the fallback.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to create events.
- **Side effects**: Creating a custom event typically triggers updates to the user's schedule and may affect the "incoming invites" or "unread" counts in the dashboard/schedule views.

## External consumers

- `NewSailingEventPage` in `concorda-web/src/app/members/events/new/page.tsx`.
