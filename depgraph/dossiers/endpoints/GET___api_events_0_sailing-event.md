---
node_id: GET::/api/events/{0}/sailing-event
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3563027e8afc062f74739c29bf322869b7658d6c2949a61452c2bd6d2037d367
status: current
---

# GET /api/events/{event_id}/sailing-event

## Purpose

Retrieves the `SailingEvent` details for a specific event, scoped to the authenticated user's relationship. Unlike a global event lookup, this method uses the caller's identity to return a version of the event data specific to them (e.g., their own boat's plan if they are a captain, or the boat they are currently crew on). This ensures that multiple captains participating in the same event see their own distinct sailing plans rather than a single global record.

## Invariants

- **Requires authentication** via `require_auth`.
- **Returns `SailingEventRead` schema**, which includes boat-specific details like `boat_sail_number` and `crew_pool_name`.
- **Scoping is identity-dependent**: The returned data is filtered by the `current_user.id` and their relationship to the boat (owner or crew).
- **Returns 404 if no relationship exists**: If the user has no valid connection to the event or its associated boats, `_get_user_sailing_event_or_404` triggers a 404.

## Gotchas

- **Identity-based visibility**: Because the endpoint relies on `_get_user_sailing_event_or_404`, a user might see a 404 even if the `event_id` is valid if they haven't been properly linked to a boat via `BoatCrew`.
- **Avoid global collisions**: Per commit `4fd165d`, the system avoids using slugs for personal events to prevent global `UNIQUE` constraint collisions in the database.
- **Crew badge visibility**: Per commit `8c29970`, the UI logic (and by extension the data returned here) is designed to suppress the "Captain" or "Crew" badge when a user is captaining their own boat to avoid redundant UI elements.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to ensure the caller is a logged-in user.
- **Side effects**: Changes to the underlying `SailingEvent` (via the sibling `PUT` method) can trigger calendar email notifications and status-based transitions.

## External consumers

- `concorda-web` (via `eventsApi.getSailingEvent`)
