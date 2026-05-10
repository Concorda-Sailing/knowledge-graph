---
node_id: DELETE::/api/admin/email-templates/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: dc232955b0ec6500ba3c7be14af012393377816b145ae350757ef09d79523a6a
status: llm_drafted
---

# DELETE /api/admin/email-templates/{template_id}

## Purpose

Permanently removes an `EmailTemplate` record from the database by its unique identifier. This is an administrative action used to clean up or replace outdated or incorrect email templates. It is distinct from the `/preview` endpoint, which only simulates rendering without modifying the database.

## Invariants

- **Requires a valid `template_id`** as a path parameter.
- **Returns a 404 error** if the template does not exist in the database.
- **Returns a JSON object** with the key `"message": "Template deleted"` upon successful deletion.
- **Performs a hard delete** via `db.delete(tpl)` and `db.commit()`.

## Gotchas

- **Admin-only access required.** While the source doesn't show the explicit guard, the path `/api/admin/` and the context of recent security-related commits (e.g., `650233f` "block privilege escalation in admin user endpoints") imply this is a protected administrative route.
- **Irreversible action.** Once the `db.commit()` is executed, the template and its associated configuration are removed from the database.

## Cross-cutting concerns

- **Auth**: Admin-level privileges required (implied by `/api/admin/` path).
- **Rate limit**: None explicitly defined for this endpoint.
- **Side effects**: Deleting a template may break any automated processes or scheduled jobs that rely on that specific `template_id` for sending notifications.

## External consumers

- `concorda-web::src/lib/api.ts::adminEmailTemplatesApi.delete` (via string_url, fuzzy, api.ts:978)
