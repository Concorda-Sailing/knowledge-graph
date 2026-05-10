---
node_id: GET::/api/events/registration-counts
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 564df74104c8f8017239856934656c969a2fb301a96430b2cb0925fefbcff63c
status: llm_drafted
---

# GET /api/events/registration-counts

## Purpose

Provides an administrative overview of event popularity by returning a mapping of event IDs to their current registration counts. This is used by admin-level dashboards to monitor engagement across the platform. It is distinct from the event detail or schedule endpoints, which focus on specific event metadata or user-centric views.

## Invariants

- **HTTP Method**: `GET`.
- **Auth Requirement**: Requires `events.edit` permission via `require_permission`.
- **Return Shape**: A dictionary where keys are `event_id` and values are integer counts (e.g., `{"uuid": 5}`).
- **Aggregation**: Uses `func.count` on `EventRegistration.id` grouped by `event_id`.

## Gotchas

- **Permission strictness**: Because it uses `require_permission("events.edit")`, this endpoint will return a 403/401 if called by a standard user, even if they are a participant in the events being counted.
- **Database dependency**: The count is a direct aggregation of the `EventRegistration` table; if the registration logic changes (e.g., moving to a different table or status-based counting), this endpoint must be updated to avoid stale metrics.

## Cross-cutting concerns

- **Auth**: Requires `events.edit` permission.
- **Side effects**: Used by the admin dashboard to visualize event engagement.

## External consumers

- `concorda-web::src/lib/api.ts::adminEventsApi.getRegistrationCounts`
