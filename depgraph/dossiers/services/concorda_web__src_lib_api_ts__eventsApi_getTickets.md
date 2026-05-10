---
node_id: concorda-web::src/lib/api.ts::eventsApi.getTickets
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d305895ed0e679d1f15a3d9d3c60f4bda0a0d04ddd3177a78afdd1632107365b
status: current
---

# eventsApi.getTickets

## Purpose

Retrieves the list of all tickets associated with a specific event via its slug. This is a read-only, unauthenticated method used to display ticket availability or registration lists on public-facing event pages. It is distinct from `getDetail`, which requires authentication and provides viewer-scoped data.

## Invariants

- **Input is an event slug.** The identifier must be the URL-friendly string (e.g., `summer-regatta-2025`), not the internal UUID.
- **Returns an array of `EventTicket` objects.** The response shape is a list of tickets, which may include registration status and pricing.
- **Uses `fetchApi` (unauthenticated).** This method does not require a bearer token and is accessible to public visitors.

## Gotchas

- **Decoupled from `getDetail`.** Per commit `1b5d864`, the API was refactored to ensure `getDetail` handles its own logic and does not rely on the coupling previously found in `mySchedule`. Ensure any logic relying on "current user context" is not accidentally placed here, as this call is public.

## Cross-cutting concerns

- **Auth**: None (Public endpoint).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `PublicEventPage` to render ticket-related information.

## External consumers

- `concorda-web::src/app/events/[slug]/page.tsx` (via `PublicEventPage`)
