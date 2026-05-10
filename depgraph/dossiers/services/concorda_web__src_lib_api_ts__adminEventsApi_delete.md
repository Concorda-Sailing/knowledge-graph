---
node_id: concorda-web::src/lib/api.ts::adminEventsApi.delete
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 670830ec8ee9ee8818b1c8ab9e825811ba2dcf829e37d993fa788cd35774b273
status: current
---

# adminEventsApi.delete

## Purpose

The `delete` method performs a destructive removal of an event resource via a `DELETE` request to `/api/events/{id}`. It is used when an administrator or system process needs to purge an event entirely from the system. This is distinct from `deleteImage`, which only removes an associated image asset, or `update`, which modifies event properties.

## Invariants

- **Method is `DELETE`** — The request must use the strict `DELETE` verb.
- **Requires authentication** — Uses `fetchApiAuthenticated`, meaning a valid bearer token is required.
- **Returns `void`** — The API response is expected to be empty (or a 204 No Content), though the client-side type is explicitly `void`.
- **Target is a single ID** — The function accepts exactly one `id: string`.

## Gotchas

- **Destructive action** — Deleting an event is a permanent operation. Ensure the UI provides a confirmation step before calling this, as there is no "undo" or "soft delete" mechanism visible in this service layer.

## Cross-cutting concerns

- **Auth**: Requires `fetchApiAuthenticated` (bearer token).
- **Side effects**: Deleting an event may impact the visibility of the event in the `schedule-card` and `regatta detail` views.

## External consumers

- `SocialsPage` in `src/app/members/admin/events/socials/page.tsx`.
