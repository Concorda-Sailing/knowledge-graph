---
node_id: concorda-web::src/lib/api.ts::adminEmailTemplatesApi.preview
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 873e9628530870dc6165468a6d8a37a23f1505497fcdb15e47b0e2f7bb1ac9fb
status: llm_drafted
---

# adminEmailTemplatesApi.preview

## Purpose

Generates a preview of a specific email template by fetching its subject and body content. This is used by the admin interface to allow administrators to verify the visual and textual integrity of a template before it is sent to end-users. It is distinct from the `update` or `delete` methods in the same object, which modify the template structure itself.

## Invariants

- **HTTP Method is `POST`** — despite being a read-only preview, it uses `POST` to match the backend endpoint contract.
- **Requires a valid `id`** — the template ID must be passed as a path parameter.
- **Returns a specific shape** — the response must contain exactly `{ subject: string; body: string }`.
- **Uses `fetchApiAuthenticated`** — requires a valid admin session/token to execute.

## Gotchas

- **Admin-only access** — because this uses `fetchApiAuthenticated`, it is strictly gated by the admin role-based access control (RBAC) logic handled by the server-side middleware.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiicated` (admin-level credentials required).
- **Side effects**: Changes to the template via `update` will immediately change the output of this `preview` call.

## External consumers

- `EmailTemplatesPage` in `concorda-web/src/app/members/admin/email/templates/page.tsx`.

## Open questions

- None.
