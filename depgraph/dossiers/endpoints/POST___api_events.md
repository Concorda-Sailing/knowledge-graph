---
node_id: POST::/api/events
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2a07bff8f6527d203ce9c3394948a66d273797665b0704c4562e17d2e00c04f9
status: current
---

# POST /api/events

## Purpose

Creates a new event record in the database. This endpoint handles the logic for categorizing events (social, personal, etc.), generating unique slugs, and assigning ownership. Use this when a user or admin needs to register a new event, noting that the logic for ownership and category-specific routing (like regattas) is strictly enforced here.

## Invariants

- **Requires `events.create` permission** via the `require_permission` dependency.
- **Returns `EventRead` shape** via `_build_event_response`.
- **Category validation is mandatory.** If `category` is not in `VALID_CATEGORIES`, a 400 error is raised.
- **Regatta creation is restricted.** If `category == "regatta"`, the request fails; regattas must be created via `POST /api/events/regattas/`.
- **Ownership is enforced.** For `personal` events, `owner_id` is forced to the `current_user.id` to prevent spoofing.
- **Slug generation is idempotent but must be unique.** The `ensure_unique_slug` function is called to prevent collisions.

## Gotchas

- **Slug collision risk for personal events.** Per commit `4fd165d`, the system drops the slug for personal events to avoid global `UNIQUE` constraint collisions in the database.
- **Strict category routing.** Attempting to create a regatta through this endpoint will fail with a 400 error; this is a deliberate guard to ensure regatta-specific logic is used.
- **Ownership spoofing prevention.** If a user attempts to set an `owner_id` that is not their own for a non-personal event, the `owner_id` is silently overwritten to the `current_user.id` unless the user has `system_admin` or `org_admin` roles.

## Cross-cutting concerns

- **Auth**: Requires `events.create` permission.
- **Side effects**: Triggers the creation of `organizing_authority_uuids` via `set_event_oas` if provided in the payload.

## External consumers

- `concorda-web::src/lib/api.ts::adminEventsApi.create` (via `http_call`)
