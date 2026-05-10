---
node_id: DELETE::/api/events/my-schedule/series/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1a2fb1e4288ee309eab686da8b7f68207aaa78697bbfb3ce8b08f9e0869f0d36
status: current
---

# DELETE /api/events/my-schedule/series/{series_uuid}

## Purpose

Removes all race-related entries for a specific series from the authenticated user's schedule. It performs a two-stage cleanup: first, it identifies all `Event` records belonging to the provided `series_uuid` that are categorized as "regatta"; second, it iterates through these events to tear down `SailingEvent` data and associated crew members if the user is the owner, before finally deleting the user's personal `PersonEvent` bookmark. This is distinct from single-event removal as it handles the cascading destruction of ownership-linked data to prevent orphaned `SailingEvent` records.

## Invariants

- **Method**: `DELETE`
- **Auth**: Requires `current_user` via `require_auth`.
- **Input**: `series_uuid` must be a valid string.
- **Return Shape**: Returns a dictionary containing `removed` (count of `PersonEvent` bookmarks deleted) and `crew_removed` (count of crew members removed via `_cleanup_sailing_event`).
- **Atomicity**: The process uses `db.commit()` after the loop, ensuring the series-wide removal is treated as a single transaction.

## Gotchas

- **Ownership-scoped cleanup**: `_cleanup_sailing_event` only deletes `SailingEvent` data if the `current_user` is the `owner` of the boat associated with that event. If a user is just a crew member, only their `PersonEvent` bookmark is removed, leaving the `SailingEvent` intact.
- **Email side effects**: The cleanup process triggers `_send_calendar_email_for_crew` for all `active_crew` (status: `invited`, `accepted`, or `confirmed`) before the data is destroyed.
- **Category restriction**: The logic only targets events where `Event.category == "regatta"`. Other event types within a series are not processed by this specific endpoint.
- **Revert history**: The logic regarding whether to include user-owned personal events is sensitive; see commit `57f2e00` and `7570175` which highlight the complexity of managing user-owned vs. viewer-owned event visibility in the schedule.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` to identify the `current_user`.
- **Websocket**: None.
- **Audit**: Y (via `_send_calendar_email_for_crew` which acts as a notification/audit trail for event cancellation).
- **Rate limit**: None.
- **Side effects**: Triggers cancellation emails to `active_crew` via `_send_calendar_email_for_crew`.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.removeScheduleSeries`
