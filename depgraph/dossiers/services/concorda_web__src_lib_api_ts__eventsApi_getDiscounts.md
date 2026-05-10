---
node_id: concorda-web::src/lib/api.ts::eventsApi.getDiscounts
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 152bf43581ab446abc59efdc959d92ffc0b48032549fdff47c39c7fe06065146
status: llm_drafted
---

# eventsApi.getDiscounts

## Purpose

Fetches the list of public discounts available for a specific event via its slug. This is a public-facing endpoint used to display promotional pricing or special offers on the event's landing page. Unlike `getDetail`, which requires authentication and returns viewer-specific context, this method is intended for unauthenticated or general viewing.

## Invariants

- **Input is an event slug.** The method expects a string representing the unique identifier for the event.
- **Returns an array of `EventDiscountPublic`.** The response shape is optimized for public display and does not include sensitive pricing or owner-only metadata.
- **Uses `fetchApi` (unauthenticated).** This method does not require a bearer token or any user-specific session-based headers.

## Gotchas

- **Slug-based routing.** The endpoint relies on the `/api/events/slug/{slug}/discounts` pattern; ensure the slug is correctly encoded if passed from a dynamic route to avoid 404s.

## Cross-cutting concerns

- **Auth**: None (publicly accessible).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: N/A.

## External consumers

- `PublicEventPage` in `concorda-web/src/app/events/[slug]/page.tsx`.
