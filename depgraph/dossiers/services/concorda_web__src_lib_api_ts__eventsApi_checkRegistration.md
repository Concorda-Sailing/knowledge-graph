---
node_id: concorda-web::src/lib/api.ts::eventsApi.checkRegistration
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 344df2b2668472589981b3ac5952576537cce4aa42a972267b30fbbc65e6a6f9
status: llm_drafted
---

# eventsApi.checkRegistration

## Purpose

The `checkRegistration` method verifies if a specific email address is associated with any of the provided product IDs for a given event slug. It is used by the public-facing event pages to determine if a visitor has already registered or to validate registration eligibility before a user attempts to sign up. It is distinct from `register` or `getConfirmation` as it is a read-only, non-authenticated check intended for pre-registration flows.

## Invariants

- **Method is `POST`** — despite being a "check" operation, it uses POST to safely pass the `product_ids` array in the request body.
- **Input requires `slug` and `email`** — the `slug` identifies the event, and the `email` is the primary lookup key.
- **Returns a boolean-wrapped response** — the shape is `{ ok: boolean; error?: string }`.
- **Does not require authentication** — uses `fetchApi` rather than `fetchApiAuthenticated`, allowing public access for unauthenticated visitors.

## Gotchas

- **Product ID dependency** — the check is scoped to specific `product_ids`. If the client fails to pass the correct IDs, the registration status might return `ok: false` even if the user has a valid registration for a different product within the same event.
- **Slug-based routing** — the endpoint is strictly tied to the event slug; any mismatch in the slug path will result in a 404 or 405 error before the logic even executes.

## Cross-cutting concerns

- **Auth**: None (Publicly accessible via `fetchApi`).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Used by `PublicEventPage` (page.tsx:297) to drive the conditional rendering of registration-related UI components.

## External consumers

- `concorda-web::src/app/events/[slug]/page.tsx::PublicEventPage`

## Open questions

- Should this be converted to a `GET` request with query parameters to allow for better caching at the CDN level, given that it is a public-facing check?
