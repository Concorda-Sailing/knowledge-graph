---
node_id: concorda-web::src/lib/api.ts::eventsApi.getConfirmation
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6ae121738caee7261c271ca4bcd26dccc932e45af52b9154ef6f88fb4c868a83
status: llm_drafted
---

# eventsApi.getConfirmation

## Purpose
`getConfirmation` retrieves registration details for a specific user via a registration ID and an event slug. It is used to display post-registration success states or verify registration status without requiring full authentication. Use this function when you need to display a "confirmation" view for a public event page, as it returns an array of registration objects (typically containing one entry) rather than a single object.

## Invariants
* HTTP Method: GET.
* Path: `/api/events/slug/${slug}/confirmation?reg=${encodeURIComponent(regId)}`.
* Returns an array of objects containing `id`, `first_name`, `email`, `status`, `created`, `ticket_name`, and `ticket_price`.
* `transaction_id` is an optional field in the returned objects.

## Gotchas
* The function returns an array (`[]`) rather than a single object, even though it is conceptually a single registration lookup; consumers must handle the array index (e.g., `data[0]`).
* The `regId` must be URI encoded before being passed to the query parameter to prevent path/query breakage.

## Cross-cutting concerns
* This is a public-facing endpoint (uses `fetchApi` rather than `fetchApiAuthenticated`), meaning it does not require a session/JWT but relies on the `regId` for data retrieval.

## External consumers
* concorda-web::src/app/events/[slug]/page.tsx (PublicEventPage)

## Open questions
* None.
