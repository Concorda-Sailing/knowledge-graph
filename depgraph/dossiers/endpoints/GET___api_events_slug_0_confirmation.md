---
node_id: GET::/api/events/slug/{0}/confirmation
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6ac37cefe63f1e9910fc18893a087e1fc5c8ed4b00918ce36de3387075808a28
status: current
---

# GET /api/events/slug/{slug}/confirmation

## Purpose

Retrieves registration confirmation details for a specific event using a slug and a registration ID. This endpoint is used by the frontend to display a "success" or "confirmation" view to a user after they have completed a registration, ensuring they can see their ticket details (price, name, status) without needing to navigate the full dashboard.

## Invariants

- **Returns a list of `EventRegistrationConfirmation` objects.** Even if only one registration is expected, the response is a JSON array.
- **Requires `slug` and `reg` query parameters.** The `reg` parameter is the registration ID used to locate the specific record.
- **Strict ownership/admin check.** A user can only access this data if they are the owner of the registration (matching `email` or `person_id`) or if they hold `system_admin` or `org_admin` roles.
- **Returns empty list on missing registration.** If the `reg` ID does not exist for the given event/slug combination, it returns `[]` rather than a 404 or error.

## Gotchas

- **Permission Denied vs. Not Found.** If a user attempts to access a registration that exists but does not belong to them, the API raises a `403 Forbidden` rather than a `404 Not Found` to prevent leaking the existence of registrations via enumeration.
- **Slug collision risk.** Per commit `4fd165d`, the system uses slugs for personal events carefully; ensure that any logic relying on this endpoint respects the distinction between event-specific slugs and global identifiers to avoid `UNIQUE` constraint collisions.

## Cross-cutting concerns

- **Auth**: Uses `get_current_user` with a tiered permission check (Owner/Admin vs. System Admin/Org Admin).
- **Side effects**: Used by the frontend to render the post-registration success state.

## External consumers

- `concorda-web` (via `eventsApi.getConfirmation`)
