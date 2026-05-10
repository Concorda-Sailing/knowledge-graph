---
node_id: GET::/api/events
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 60bcc82d3a4a650b1c92c0499b9090272642fe693158c8736a33d01c3fa03e06
status: llm_drafted
---

# GET /api/events

## Purpose

Provides the primary interface for retrieving event lists, including upcoming public events, filtered by date, region, or category. It serves as the data source for both the global event discovery view and the user-specific schedule view. Use this endpoint when you need to populate calendars, event feeds, or personal schedules.

## Invariants

- **Default visibility is public.** If no `category` is provided, the query filters out all events where `category == "personal"`.
- **Returns `EventReadWithRegatta` objects.** The response shape is a list of objects that include enriched sailing/regatta details.
- **Ordering is strictly chronological.** All list-based responses are ordered by `Event.date` to ensure consistent UI rendering.
- **`get_my_schedule` requires authentication.** It depends on `require_auth` to fetch the `current_user`.

## Gotchas

- **Personal event visibility.** Per commit `7570175`, the API must explicitly exclude "personal" category events unless a specific category is requested, otherwise, private user events would leak into global lists.
- **Date flooring for schedules.** Per commit `559491c`, the `my-schedule` logic uses a "start-of-today" floor rather than a strict `now()` comparison. This ensures events created or updated earlier in the current UTC day are not missed by the user.
- **Slug collisions.** Per commit `4fd165d`, personal events must not use the same slug format as public events to avoid `UNIQUE` constraint violations in the database.
- **Registration counts permission.** The `/registration-counts` sub-route requires the `events.edit` permission via `require_permission`.

## Cross-cutting concerns

- **Auth**: `get_my_schedule` requires `require_auth`; `/registration-counts` requires `events.edit` permission.
- **Side effects**: The `schedule detail page` depends on the data structure returned by the `slug` sub-route.

## External consumers

- `concorda-web` (via `socialsApi.list`)
- `concorda-test` (via `ApiClient.listEvents`)
