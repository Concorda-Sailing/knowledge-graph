---
node_id: concorda-web::src/lib/api.ts::adminEmailTemplatesApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: f2a7f418aa457c507af851456e9d21461f359643e1634bfcde05b5b7d075dfd0
status: current
---

# adminEmailTemplatesApi.create

## Purpose

Provides the interface for creating new email templates within the admin dashboard. This method sends a `POST` request to the `/api/admin/email-templates` endpoint with the required template metadata. It is used exclusively by the admin-facing template management UI to persist new communication styles.

## Invariants

- **Method is `POST`** — uses `fetchApiAuthenticated` to ensure the request is authorized.
- **Payload structure** — requires `name`, `subject`, and `body` as strings.
- **Returns `EmailTemplate`** — a successful creation returns the fully formed template object from the server.
- **`variables` is optional** — the `variables` array can be omitted or empty, but if provided, it defines the placeholders available for the template.

## Gotchas

- **Admin-only access** — relies on `fetchApiAuthenticated`, meaning the caller must have administrative privileges.
- **Template variable consistency** — while the API accepts a `variables` array, the actual rendering of these variables is handled by the backend; ensure the `body` string matches the expected variable syntax used by the email engine.

## Cross-cutting concerns

- **Auth**: Requires an authenticated admin session via `fetchApiAuthenticated`.
- **Side effects**: Creating a template here updates the available options for the email dispatching system used by the backend.

## External consumers

- `EmailTemplatesPage` in `src/app/members/admin/email/templates/page.tsx`.
