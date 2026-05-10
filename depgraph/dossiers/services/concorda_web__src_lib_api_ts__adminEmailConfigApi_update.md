---
node_id: concorda-web::src/lib/api.ts::adminEmailConfigApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1631bf347738b031a662aae92fd25a1162c0dd28f933a11aa3f55ac693c067d8
status: current
---

# adminEmailConfigApi.update

## Purpose

Updates the global email configuration settings for the organization. This method is used to modify properties like `support_email`, `web_base_url`, and `mode`. It is distinct from `adminEmailTemplatesApi`, which manages the content of individual email messages; this method manages the infrastructure-level settings that govern how and where those emails are sent.

## Invariants

- **Method is `PUT`** — Uses a single `PUT` request to the `/api/admin/email-config` endpoint.
- **Requires `fetchApiAuthenticated`** — The call must be wrapped in the authenticated fetch helper to include the necessary bearer token.
- **Input is a `Partial<EmailConfigData>`** — Only the fields provided in the payload are updated; it does not require a full object, but the API expects the shape of `EmailConfigData`.
- **Returns `EmailConfigData`** — The response contains the updated configuration object.

## Gotchas

- **Admin privilege requirement** — Because this uses `fetchApiAuthenticated` on an `/api/admin/` path, the user must have an administrative role. Failure to ensure the user is an admin will result in a 401 or 403 error.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Updates to this config (specifically `web_base_url` or `mode`) may affect how links are generated in emails sent via `adminEmailTemplatesApi` or `sendBulk`.

## External consumers

- `AdminEmailPage` in `src/app/members/admin/email/page.tsx`.
