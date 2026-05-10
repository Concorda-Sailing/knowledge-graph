---
node_id: concorda-web::src/lib/api.ts::adminEmailTemplatesApi.delete
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0659a572e9cfbe184504853193403d54570cc78f12365ab4e21a918b168ff194
status: llm_drafted
---

# adminEmailTemplatesApi.delete

## Purpose

Deletes a specific email template from the system. It is part of the `adminEmailTemplatesApi` group, which manages the lifecycle of automated email communications. Use this method when an administrator needs to permanently remove a template by its unique identifier.

## Invariants

- **Method is `DELETE`** — The request must use the `DELETE` verb to target the specific template resource.
- **Requires a valid `id`** — The function takes a single string argument representing the template's unique identifier.
- **Returns a success message** — The response shape is `{ message: string }`.
- **Uses `fetchApiAuthenticated`** — The call is wrapped in the authenticated fetch helper, requiring a valid session/token.

## Gotchas

- **Admin-only access** — Because this is part of the `adminEmailTemplatesApi` group, it relies on `fetchApiAuthenticated`. Unauthorized users or non-admin roles attempting to call this will fail at the API layer.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Audit**: N/A.
- **Side effects**: Deleting a template may break existing automated flows that rely on that specific template ID for scheduled or event-driven notifications.

## External consumers

- `concorda-web::src/app/members/admin/email/templates/page.tsx` (EmailTemplatesPage)

## Open questions
