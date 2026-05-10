---
node_id: concorda-web::src/lib/api.ts::adminEventDiscountsApi.list
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 619747f9c284e40c4273cd79697d84ce22c54540e5bc2941f186d91c563409c2
status: llm_drafted
---

# adminEventDiscountsApi.list

## Purpose

Provides an administrative interface for managing event-specific discounts. This method retrieves the list of available discounts for a given `eventId`, serving as the read-only entry point for the admin-side discount management UI. It is distinct from the `paymentsApi` which handles the actual creation of payment intents and client-side secrets.

## Invariants

- **Requires `eventId`** — The path parameter must be a valid event identifier to resolve the correct discount collection.
- **Uses `fetchApiAuthenticated`** — This is an administrative endpoint; it requires a valid bearer token and will fail if the user is not authenticated.
- **Returns `EventDiscount[]`** — The response is a collection of discount objects, which may include fields like `code`, `membership_id`, and `max_uses`.

## Gotchas

- **Administrative access required** — Because this uses `fetchApiAuthenticated`, any UI component calling this must ensure the user has the appropriate administrative permissions, or the request will fail with a 401/403.
- **Dependency on event existence** — If the `eventId` provided does not exist or the event has been deleted, the API will return a 404.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin session).
- **Side effects**: Changes to discounts via sibling methods (`create`, `update`, `delete`) will affect the pricing/checkout flow for the specific event.

## External consumers

- `concorda-web::src/app/members/admin/events/[id]/page.tsx` (via `EventDetailContent`)
