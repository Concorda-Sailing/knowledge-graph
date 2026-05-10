---
node_id: POST::/api/events/custom
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5d32f8d81f65de3a2a03d33c8cc4d9b88534ed8a6653ffcde6c727c791ed7c7f
status: llm_drafted
---

# POST /api/events/custom

## Purpose

Creates a personal sailing event (e.g., training, cruise, or delivery) that is tied to a specific user but not necessarily a public organization event. It pops an `Event` record for the general calendar and a `SailingEvent` record for specific maritime metadata (locations, times, and roles). Use this instead of standard event creation when the event is a "personal" category item that should not require an organization context.

## Invariants

- **Requires Authentication** — Uses `require_auth` to identify the `current_user`.
- **Mandatory `boat_uuid` Ownership** — If `data.boat_uuid` is provided, the caller must pass the `_require_boat_owner` check.
- **Returns a Dictionary** — The response shape is a `dict` containing both the `event` (EventRead) and the `sailing_event` (via `_sailing_event_to_read`).
- **Category is Hardcoded** — The `category` is explicitly set to `"personal"` and the `slug` is set to `None`.

## Gotchas

- **Slug Collision Risk** — Per commit `4fd165d`, the `slug` is explicitly set to `None` to avoid `UNIQUE` constraint collisions in the global events table, as personal events are not intended to have public-facing slugs.
- **Ownership Enforcement** — The function calls `_require_boat_owner` if a `boat_uuid` is present; if the user is not the owner, it raises a 403. This is a critical guard for preventing unauthorized boat-linked event creation.
- **Two-Stage Commit** — The function performs a `db.add(event)` followed by a `db.add(se)` and a final `db.commit()`. The `event.id` is used to link the two records.

## Cross-cutting concerns

- **Auth**: Requires `current_user` via `require_auth`.
- **Side effects**: Creates records that populate the user's personal schedule and the general event calendar.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.createCustom`
- `concorda-test::lib/api-client.ts::ApiClient.createSailingEvent`
