---
node_id: concorda-web::src/lib/api.ts::adminEmailTemplatesApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 989405550d4288e531d761964376f7d28be9f402b3befcf516cb7c98727f7c58
status: current
---

# adminEmailTemplatesApi.update

## Purpose

Provides the interface for updating existing email templates in the admin dashboard. It allows for partial updates to a template's metadata (name, subject, body, description) and its configuration (active status, available variables). This is distinct from the `create` method, which requires the full object shape.

## Invariants

- **Method is `PUT`** — Uses the `PUT` verb to perform partial updates on a specific template resource.
- **Requires a valid `id`** — The first argument must be the unique identifier for the template being modified.
- **Uses `fetchApiAuthenticated`** — All calls must be authenticated via the admin session.
- **Input is a `Partial` of the template shape** — Only the fields provided in the `data` object are updated; omitted fields are not cleared but depend on the backend's implementation of `PATCH` vs `PUT` semantics.

## Gotchas

- **Template ID dependency** — If the `id` passed is incorrect or the template has been deleted, the request will fail.
- **`fetchApiAuthenticated` requirement** — Because this is an admin-only endpoint, the caller must ensure the user has the appropriate administrative permissions before attempting the update.

## Cross-cutting concerns

- **Auth**: Requires admin-level authentication via `fetchApiAuthenticated`.
- **Side effects**: Updates to template content or `is_active` status directly affect the content of outgoing system emails (e.g., event invitations or status updates).

## External consumers

- `EmailTemplatesPage` in `src/app/members/admin/email/templates/page.tsx`.
