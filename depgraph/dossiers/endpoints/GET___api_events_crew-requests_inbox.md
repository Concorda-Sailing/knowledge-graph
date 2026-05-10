---
node_id: GET::/api/events/crew-requests/inbox
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9b3a93c8280b6897135a2e4ed4c34324fa628dfc5589c28a8ef559751b478669
status: llm_drafted
---

# GET /api/events/crew-requests/inbox

## Purpose

Provides a list of pending crew requests directed at the authenticated user. It specifically filters for `EventCrew` rows where the status is `requested` and the user is the `owner` of the associated boat. This allows captains to manage incoming requests via a centralized Inbox without navigating to specific event detail pages.

## Invariants

- **Requires authentication** via the `require_auth` dependency.
- **Returns an array of objects** containing `event_crew_id`, `event_id`, `event_name`, `event_date`, `event_slug`, `boat_id`, `boat_name`, `boat_sail_number`, `requester_id`, `requester_first_name`, `requester_last_name`, `requester_picture_url`, `notes`, and `requested_at`.
- **Filters by future events only.** The query includes `Event.date >= datetime.now(timezone.utc)` to ensure the inbox does not display stale requests for completed races.
- **Ownership check is mandatory.** A user only sees requests for boats where they hold the `role == "active"` and `role == "owner"` status.

## Gotchas

- **Date filtering logic is sensitive.** Per commit `559491c`, the system must floor filters at the start-of-today to avoid missing requests due to time-of-day discrepancies.
- **Visibility is tied to boat ownership.** If a user is not an "owner" or is not "active" on the `BoatCrew` row, the list returns empty even if requests exist.
- **Slug collision prevention.** Per commit `4fd165d`, the endpoint relies on the fact that personal events have dropped slugs to avoid global `UNIQUE` constraint collisions in the database.

## Cross-cutting concerns

- **Auth**: Uses `require_auth` to identify the `current_user`.
- **Side effects**: This is a read-only endpoint, but it is the primary data source for the "Inbox" feature in the web UI.

## External consumers

- `concorda-web::src/lib/api.ts::eventsApi.listInboxCrewRequests`
