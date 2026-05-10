---
node_id: concorda-web::src/lib/api.ts::eventsApi.checkin
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: eace4a33568835389ebd35c5e94ea31daee2003a0f90750d082c651a9bced0ae
status: current
---

# eventsApi.checkin

## Purpose

The `checkin` method handles the administrative action of marking a specific registration as "checked in" for an event. It is distinct from `checkRegistration`, which is a read-only/validation-only check used to verify if an email/product combination is valid. Use this method when a user (typically an admin or organizer) is physically present at an event and needs to update the registration status to reflect attendance.

## Invariants

- **Method is `POST`** — Requires a POST request to the `/api/events/slug/${slug}/checkin` endpoint.
- **Requires `fetchApiAuthenticated`** — This is a protected action; the caller must have a valid session/token.
- **Input is `regId`** — The function accepts a single string representing the registration ID.
- **Returns registration details** — The response shape includes `id`, `first_name`, `last_name`, `email`, `status`, `ticket_name`, and `checked_in_at`.

## Gotchas

- **Dependency on `slug`** — The endpoint is keyed by the event slug, not a UUID, so ensure the slug is correctly resolved before calling.
- **Status updates are permanent** — Once `checked_in_at` is populated, the registration state changes.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` to ensure the user has permission to perform administrative check-ins.
- **Side effects**: Successful check-ins may affect the visibility of attendance status on the event detail page.

## External consumers

- `CheckinPage` in `src/app/events/[slug]/checkin/page.tsx` (via `hook_call`).
