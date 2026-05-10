---
node_id: concorda-web::src/lib/api.ts::eventsApi.getMyRegistration
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9729d8a9d0f8ec28b6d8fad095962d0d04d70d82e9ec1ea1f9562a927add33fd
status: llm_drafted
---

# eventsApi.getMyRegistration

## Purpose

Retrieves the registration details for the currently authenticated user for a specific event. It returns an array of registration objects (allowing for multiple tickets/roles under one identity) containing identity, status, and pricing information. Use this when a component needs to display a user's personal participation status (e.g., "You are registered as [Role]") on an event detail page.

## Invariants

- **Requires authentication** — Uses `fetchApiAuthenticated` and requires a valid bearer token.
- **Input is a slug** — The identifier is the event's URL-friendly slug, not the numeric ID.
- **Returns an array** — Even if the user has only one registration, the return type is `Array<{...}>`.
- **Field contract** — Includes `ticket_name`, `ticket_price`, and `status` to allow UI to differentiate between "Registered", "Pending", or "Paid" states.

## Gotchas

- **Identity-based filtering** — This is a viewer-scoped call; it only returns data relevant to the authenticated user's claims for the specific event.
- **Coupling with `getDetail`** — Per commit `1b5d864`, the system moved away from coupling `mySchedule` with the general detail view to ensure the detail page remains functional even if registration state is being fetched separately.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`; requires a valid session/token.
- **Side effects**: Used by `PublicEventPage` and `ScheduleEventDetail` to render personalized registration status and ticket info.

## External consumers

- None known.
