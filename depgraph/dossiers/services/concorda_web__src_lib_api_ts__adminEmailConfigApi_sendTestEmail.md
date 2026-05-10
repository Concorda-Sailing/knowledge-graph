---
node_id: concorda-web::src/lib/api.ts::adminEmailConfigApi.sendTestEmail
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8bdfa943e1c391cb3f300f8b9532d0228899f18d82ff95bb03dce409fc2d2f36
status: current
---

# adminEmailConfigApi.sendTestEmail

## Purpose

Triggers a single-recipient test email to verify the current email configuration (SMTP/provider settings) is functional. It is a diagnostic tool used by administrators to ensure that the system can successfully reach external mail servers before relying on automated notifications. Use this instead of `sendBulk` when testing connectivity or template rendering with a single address.

## Invariants

- **Method is `POST`** to `/api/admin/email-config/test`.
- **Requires `fetchApiAuthenticated`** — the caller must be an authenticated administrator.
- **Input is a single string** representing the `to_email` destination.
- **Returns a JSON object** with the shape `{ message: string }`.

## Gotchas

- **Requires admin-level authorization** via `fetchApiAuthenticated`. If the user lacks the proper role, the request will fail at the API level, though the client-side error handling is not explicitly defined in this snippet.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Triggers an actual outbound email via the configured mail provider.

## External consumers

- `concorda-web::src/app/members/admin/email/page.tsx::AdminEmailPage`
