---
node_id: GET::/api/boats/{0}/events
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a7baf78428fcb79b50ced05fe0311497f8cbb31f3f0278378aa0f17e537ca800
status: llm_drafted
---

# GET /api/boats/{boat_id}/events

## Purpose

Returns a list of regattas/events a specific boat is currently signed up for. It aggregates data from `RegattaIntent` and the associated `Regatta` model to provide a high-level view of a boat's schedule, including status and position requirements. Use this endpoint to populate boat-specific calendars or schedule views.

## Invariants

- **HTTP Method**: `GET`.
- **Auth Requirement**: Requires a valid session via `require_auth`.
- **Access Control**: Returns `403 Forbidden` if the user is not a member of the boat or if the membership status is not `active` or `invited`.
- **Return Shape**: Returns a list of `BoatEventRead` objects containing `intent_id`, `regatta_uuid`, `regatta_name`, `event_date`, and `status`.
- **Data Source**: Joins `RegattaIntent` with the `Regatta` table to resolve names and dates.

## Gotchas

- **Membership Status Sensitivity**: Access is strictly gated by `membership.status`. Per commit `36ef425`, the authorization logic was tightened; users with "pending" or "staged" statuses may be blocked from seeing events even if they are part of the crew workflow.
- **Implicit 404**: The endpoint calls `_get_boat_or_404` before checking membership. If the `boat_id` is invalid, it returns a 404 rather than a 403.

## Cross-cutting concerns

- **Auth**: Guarded by `require_auth` and `_get_crew_membership`.
- **Side effects**: None.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.getEvents`
