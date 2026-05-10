---
node_id: concorda-web::src/lib/api.ts::adminEmailConfigApi.sendBulk
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 74ef895ce04b4c2a3acf2ea4f0902a3fef4e7a268dd3b9b7bd00eadc1e4418a3
status: current
---

# adminEmailConfigApi.sendBulk

## Purpose

Triggers a bulk email broadcast to a set of recipients. It is used by administrators to send templated or custom-body messages to multiple product-related recipients simultaneously. Use this instead of `sendTestEmail` when you need to target specific `product_ids` or `delegates`.

## Invariants

- **HTTP Method**: `POST` to `/api/admin/email/send`.
- **Authentication**: Requires a valid session via `fetchApiAuthenticated`.
- **Payload Shape**: Accepts an object containing optional `subject`, `body`, `template_id`, `product_ids` (array of strings), and `include_delegates` (boolean).
- **Return Shape**: Returns a `BulkEmailResult` containing `sent`, `failed`, `total_recipients`, and an `errors` array of `{ email, error }` objects.

## Gotchas

- **Bulk failures are partial**: The API returns a `BulkEmailResult` rather than throwing on individual recipient failures. The caller must inspect the `errors` array to determine if the broadcast was partially successful.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges via `fetchApiAuthenticated`.
- **Audit**: (Y) Triggering a bulk send is an administrative action; ensure any UI-level logging or backend audit trails are respected.
- **Side effects**: Primarily affects the delivery of communications to members/product-owners.

## External consumers

- `ComposeEmailPage` in `src/app/members/admin/email/compose/page.tsx`.
