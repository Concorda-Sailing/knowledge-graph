---
node_id: concorda-web::src/lib/api.ts::adminEventDiscountsApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3a3b2767cc9cf8d3827b213f4f7e4863bb1a1607350ae50e8684b939767abe86
status: llm_drafted
---

# adminEventDiscountsApi.create

## Purpose

Provides the administrative interface for managing event-specific discounts. This method handles the creation of a new discount record for a specific event, allowing admins to define pricing incentives like `ticket_ids`, `is_active` status, and `max_uses` limits. It is distinct from the `paymentsApi` which handles the client-side intent creation; this is a backend-facing administrative tool.

## Invariants

- **Method is `POST`** — uses `fetchApiAuthenticated` to ensure the request is authorized.
- **Path is event-scoped** — requires a valid `eventId` to construct the URL `/api/events/${eventId}/discounts`.
- **Payload is `EventDiscountCreate`** — the body must match the expected shape of the `EventDiscountCreate` interface.
- **Returns `EventDiscount`** — a successful call returns the newly created discount object.

## Gotchas

- **Admin-only access** — relies on `fetchApiAuthenticated`, meaning the caller must have administrative privileges.
- **Event-dependency** — if the `eventId` provided does not exist or is not associated with a valid event, the API will return a 404 or 400 error.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session via `fetchApiAuthenticated`.
- **Side effects**: Modifying discounts via this method will affect the `paymentsApi.createEventIntent` logic, as discounts are applied during the payment intent creation process.

## External consumers

- `concorda-web::src/app/members/admin/events/[id]/page.tsx` (via `EventDetailContent`)
